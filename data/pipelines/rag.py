"""RAG: chunk, embed, retrieve, and generate answers from Brasaland manuals.

Public generation helpers: ``generate_answer(question, chunks)`` (retrieval-free)
and ``query(question)`` (retrieve + generate). Indexing is operator-run via
``scripts/index_knowledge_base.py`` → ``setup()`` (not FastAPI lifespan).
"""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import Any

COLLECTION_NAME = "brasaland_knowledge"
VECTOR_SIZE = 384
DEFAULT_MIN_SCORE = 0.55
DEFAULT_TOP_K = 5
COMPANY = "brasaland"
SOURCE_DOCUMENTS = (
    "loyalty-program",
    "waste-protocol",
    "menu-allergens",
    "supplier-ordering",
)
DEFAULT_EMBED_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_GATEWAY_BASE = "https://llm.4geeks.ai/v1"

_embedder: Any | None = None

SYSTEM_PROMPT = """You are a Brasaland location salesperson helping managers and customers.
Answer ONLY using the retrieved context below. Speak confidently in a clear salesperson voice.
Rules:
- Do not invent facts, numbers, percentages, kg amounts, or policies absent from the context.
- Keep USD and COP amounts exactly as written; never convert currencies.
- For allergen questions: never say "zero risk" or guarantee zero cross-contamination; follow the allergen guide wording literally.
- Match the language of the user's question.
- If the context is empty or insufficient, say clearly that there is not enough information in the official manuals — do not guess.
"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_corpus_path() -> Path:
    """Return corpus directory from env or repo-relative default."""
    configured = os.environ.get("KNOWLEDGE_CORPUS_PATH", "").strip()
    if configured:
        path = Path(configured).expanduser()
        return (path if path.is_absolute() else _repo_root() / path).resolve()
    return (_repo_root() / "docs" / "company-knowledge-base").resolve()


def _get_embedder() -> Any:
    """Lazy-init fastembed so mocked CI never downloads a model at import time."""
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding

        model_name = os.environ.get("EMBED_MODEL_ID", DEFAULT_EMBED_MODEL)
        _embedder = TextEmbedding(model_name=model_name)
    return _embedder


def embed(text: str) -> list[float]:
    """Embed a single string. Passages: raw text. Questions: caller adds 'query: ' prefix."""
    embedder = _get_embedder()
    vectors = list(embedder.embed([text]))
    if not vectors:
        raise RuntimeError("embed: model returned no vectors")
    return [float(x) for x in vectors[0]]


def get_qdrant_client() -> Any:
    from qdrant_client import QdrantClient

    url = os.environ.get("QDRANT_URL", "http://localhost:6333").rstrip("/")
    return QdrantClient(url=url)


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _chunk_section_body(body: str, *, min_chunks_hint: int = 1) -> list[str]:
    """Split a section body on paragraphs, then sentences — never mid-sentence."""
    body = body.strip()
    if not body:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if len(paragraphs) >= max(min_chunks_hint, 2):
        return paragraphs

    if len(paragraphs) == 1 and min_chunks_hint > 1:
        sentences = _split_sentences(paragraphs[0])
        if len(sentences) >= min_chunks_hint:
            return sentences
        if len(sentences) >= 2:
            return sentences

    return paragraphs if paragraphs else [body]


def chunk_markdown(text: str, *, source_document: str) -> list[dict[str, Any]]:
    """Section-aware markdown chunking; ensure at least 3 chunks per document."""
    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_title = source_document.replace("-", " ").title()
    current_lines: list[str] = []

    heading_re = re.compile(r"^(#{1,3})\s+(.+)$")

    for line in lines:
        match = heading_re.match(line.strip())
        if match:
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = match.group(2).strip().strip('"')
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines or not sections:
        sections.append((current_title, current_lines))

    raw_chunks: list[tuple[str, str]] = []
    for title, section_lines in sections:
        body = "\n".join(section_lines).strip()
        if not body:
            continue
        for piece in _chunk_section_body(body):
            raw_chunks.append((title, piece))

    if len(raw_chunks) < 3:
        # Force more splits from the longest chunk(s) using sentences.
        expanded: list[tuple[str, str]] = []
        for title, piece in raw_chunks:
            sentences = _split_sentences(piece)
            if len(sentences) > 1 and len(raw_chunks) + len(sentences) - 1 >= 3:
                for sentence in sentences:
                    expanded.append((title, sentence))
            else:
                expanded.append((title, piece))
        raw_chunks = expanded

    if len(raw_chunks) < 3:
        # Last resort: split whole document into sentences.
        all_text = text.strip()
        sentences = _split_sentences(all_text)
        if len(sentences) >= 3:
            title = sections[0][0] if sections else source_document
            # Group sentences into ~3 chunks
            n = len(sentences)
            size = max(1, n // 3)
            raw_chunks = []
            for i in range(0, n, size):
                group = " ".join(sentences[i : i + size]).strip()
                if group:
                    raw_chunks.append((title, group))
            raw_chunks = raw_chunks[: max(3, len(raw_chunks))]

    if len(raw_chunks) < 3:
        raise ValueError(
            f"chunk_markdown: could not produce ≥3 chunks for {source_document!r} "
            f"(got {len(raw_chunks)})"
        )

    return [
        {
            "company": COMPANY,
            "source_document": source_document,
            "section": section,
            "language": "en",
            "chunk_index": index,
            "text": body,
        }
        for index, (section, body) in enumerate(raw_chunks)
    ]


def setup(*, corpus_path: Path | None = None) -> dict[str, Any]:
    """Clear-and-reload Qdrant collection from corpus markdown files.

    Idempotent: recreates the collection so re-indexing drops stale chunks.
    """
    from qdrant_client.models import Distance, PointStruct, VectorParams

    root = corpus_path if corpus_path is not None else resolve_corpus_path()
    if not root.is_dir():
        raise FileNotFoundError(f"Knowledge corpus not found: {root}")

    client = get_qdrant_client()
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )

    points: list[Any] = []
    per_doc: dict[str, int] = {}
    for stem in SOURCE_DOCUMENTS:
        path = root / f"{stem}.md"
        if not path.is_file():
            raise FileNotFoundError(f"Missing source document: {path}")
        chunks = chunk_markdown(path.read_text(encoding="utf-8"), source_document=stem)
        per_doc[stem] = len(chunks)
        for chunk in chunks:
            vector = embed(chunk["text"])
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=chunk,
                )
            )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return {
        "collection": COLLECTION_NAME,
        "points": len(points),
        "per_document": per_doc,
    }


def retrieve(
    question: str,
    *,
    k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_MIN_SCORE,
) -> list[dict[str, Any]]:
    """Embed the question with BGE query prefix; return payload dicts above min_score."""
    query_vector = embed(f"query: {question}")
    client = get_qdrant_client()
    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=k,
        with_payload=True,
    )
    hits = getattr(response, "points", response)
    results: list[dict[str, Any]] = []
    for hit in hits:
        score = float(getattr(hit, "score", 0.0) or 0.0)
        if score < min_score:
            continue
        payload = dict(getattr(hit, "payload", None) or {})
        payload["_score"] = score
        results.append(payload)
    return results


def _build_user_prompt(question: str, chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return (
            f"Question: {question}\n\n"
            "Retrieved context: (none — no chunk cleared the similarity threshold)\n\n"
            "Respond that there is not enough information in the official Brasaland manuals."
        )
    blocks: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        blocks.append(
            f"[{index}] source={chunk.get('source_document')} "
            f"section={chunk.get('section')}\n{chunk.get('text', '')}"
        )
    context = "\n\n".join(blocks)
    return f"Retrieved context:\n{context}\n\nQuestion: {question}"


def _generate(question: str, chunks: list[dict[str, Any]]) -> str:
    from openai import OpenAI

    api_key = os.environ.get("LLM_GATEWAY_API_KEY")
    if not api_key:
        raise RuntimeError("LLM_GATEWAY_API_KEY is not set")
    base_url = os.environ.get("LLM_GATEWAY_BASE_URL", DEFAULT_GATEWAY_BASE).rstrip("/")
    model = os.environ.get("GENERATION_MODEL_ID")
    if not model:
        raise RuntimeError("GENERATION_MODEL_ID is not set")

    client = OpenAI(api_key=api_key, base_url=base_url)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(question, chunks)},
        ],
        temperature=0.2,
    )
    message = completion.choices[0].message.content
    if not message:
        raise RuntimeError("generation returned empty content")
    return message.strip()


def generate_answer(question: str, chunks: list[dict[str, Any]]) -> str:
    """Generate a salesperson answer from already-retrieved chunks (no retrieval)."""
    return _generate(question, chunks)


def query(question: str, *, k: int = DEFAULT_TOP_K, min_score: float = DEFAULT_MIN_SCORE) -> str:
    """Retrieve context and generate a salesperson answer."""
    cleaned = question.strip()
    if not cleaned:
        raise ValueError("question must not be empty")
    chunks = retrieve(cleaned, k=k, min_score=min_score)
    # Strip internal score before prompting
    prompt_chunks = [{k: v for k, v in c.items() if k != "_score"} for c in chunks]
    return generate_answer(cleaned, prompt_chunks)
