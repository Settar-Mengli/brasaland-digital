"""Load and chunk public knowledge corpus from manifest allowlist only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipelines.rag import COMPANY, chunk_markdown
from pipelines.rag_profiles import PUBLIC_PROFILE

MANIFEST_NAME = "manifest.json"


@dataclass(frozen=True, slots=True)
class ManifestSource:
    path: str
    topic: str
    format: str
    audience: str
    locale: str
    last_verified_at: str


class PublicCorpusError(ValueError):
    """Invalid or disallowed public corpus source."""


def _validate_manifest_path(corpus_root: Path, rel_path: str) -> Path:
    normalized = rel_path.replace("\\", "/").strip()
    if not normalized or normalized.startswith("/"):
        raise PublicCorpusError(f"invalid manifest path: {rel_path!r}")
    parts = Path(normalized).parts
    if ".." in parts:
        raise PublicCorpusError(f"manifest path escapes corpus root: {rel_path!r}")
    resolved = (corpus_root / normalized).resolve()
    try:
        resolved.relative_to(corpus_root.resolve())
    except ValueError:
        raise PublicCorpusError(f"manifest path escapes corpus root: {rel_path!r}")
    return resolved


def load_manifest(corpus_root: Path) -> list[ManifestSource]:
    """Parse manifest.json and return allowlisted source records."""
    manifest_path = corpus_root / MANIFEST_NAME
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing public manifest: {manifest_path}")
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = raw.get("sources")
    if not isinstance(sources, list) or not sources:
        raise PublicCorpusError(f"{manifest_path}: sources must be a non-empty list")

    result: list[ManifestSource] = []
    for index, entry in enumerate(sources):
        if not isinstance(entry, dict):
            raise PublicCorpusError(f"{manifest_path}[{index}]: expected object")
        path = entry.get("path")
        topic = entry.get("topic")
        fmt = entry.get("format")
        audience = entry.get("audience")
        locale = entry.get("locale", raw.get("locale", PUBLIC_PROFILE.locale))
        verified = entry.get(
            "last_verified_at", raw.get("last_verified_at", "")
        )
        if not isinstance(path, str) or not path.strip():
            raise PublicCorpusError(f"{manifest_path}[{index}]: missing path")
        if not isinstance(topic, str) or not topic.strip():
            raise PublicCorpusError(f"{manifest_path}[{index}]: missing topic")
        if fmt not in ("json", "markdown"):
            raise PublicCorpusError(f"{manifest_path}[{index}]: invalid format")
        if audience != PUBLIC_PROFILE.audience:
            raise PublicCorpusError(
                f"{manifest_path}[{index}]: audience must be public"
            )
        _validate_manifest_path(corpus_root, path)
        result.append(
            ManifestSource(
                path=path.strip(),
                topic=topic.strip(),
                format=fmt,
                audience=audience,
                locale=str(locale).strip() if locale else PUBLIC_PROFILE.locale,
                last_verified_at=str(verified).strip() if verified else "",
            )
        )
    return result


def _public_payload_base(
    source: ManifestSource,
    *,
    record_id: str,
    section: str,
    text: str,
    chunk_index: int,
) -> dict[str, Any]:
    return {
        "company": COMPANY,
        "source_document": source.path,
        "section": section,
        "language": source.locale,
        "chunk_index": chunk_index,
        "text": text,
        "audience": source.audience,
        "topic": source.topic,
        "record_id": record_id,
        "locale": source.locale,
        "last_verified_at": source.last_verified_at,
    }


def _format_hours(regular_hours: dict[str, Any]) -> str:
    lines: list[str] = []
    for day, slot in sorted(regular_hours.items()):
        if isinstance(slot, dict):
            open_t = slot.get("open", "")
            close_t = slot.get("close", "")
            lines.append(f"{day}: {open_t}–{close_t}")
    return "\n".join(lines)


def _format_location_record(loc: dict[str, Any], source: ManifestSource) -> str:
    name = loc.get("display_name", loc.get("slug", "location"))
    lines = [
        f"Location: {name}",
        f"Slug: {loc.get('slug', '')}",
        f"Address: {loc.get('full_address', '')}",
        f"City: {loc.get('city', '')}",
        f"Country: {loc.get('country_code', '')}",
        f"Currency: {loc.get('currency', '')}",
        f"Timezone: {loc.get('timezone', '')}",
        f"Phone: {loc.get('phone', '')}",
        f"Status: {loc.get('status', '')}",
    ]
    hours = loc.get("regular_hours")
    if isinstance(hours, dict):
        lines.append("Regular hours:")
        lines.append(_format_hours(hours))
    reservations = loc.get("reservations")
    if isinstance(reservations, dict):
        lines.append(
            f"Reservations accepted: {reservations.get('accepted')}; "
            f"{reservations.get('note', '')}"
        )
    ordering = loc.get("ordering")
    if isinstance(ordering, dict):
        lines.append(
            f"Ordering: online={ordering.get('online')}, "
            f"pickup={ordering.get('pickup')}, delivery={ordering.get('delivery')}"
        )
    verified = loc.get("last_verified_at", source.last_verified_at)
    if verified:
        lines.append(f"Last verified: {verified}")
    return "\n".join(lines)


def _format_menu_item(item: dict[str, Any], source: ManifestSource) -> str:
    name = item.get("name", item.get("id", "item"))
    lines = [
        f"Menu item: {name}",
        f"ID: {item.get('id', '')}",
        f"Category: {item.get('category', '')}",
        f"Description: {item.get('description', '')}",
    ]
    price = item.get("price")
    if isinstance(price, dict):
        for currency, amount in sorted(price.items()):
            lines.append(f"Price {currency}: {amount}")
    allergens = item.get("allergens")
    if isinstance(allergens, list):
        lines.append(f"Allergens: {', '.join(str(a) for a in allergens)}")
    may_contain = item.get("may_contain")
    if isinstance(may_contain, list) and may_contain:
        lines.append(f"May contain: {', '.join(str(m) for m in may_contain)}")
    dietary = item.get("dietary_flags")
    if isinstance(dietary, list) and dietary:
        lines.append(f"Dietary: {', '.join(str(d) for d in dietary)}")
    markets = item.get("markets")
    if isinstance(markets, dict):
        active = [k for k, v in markets.items() if v]
        if active:
            lines.append(f"Markets: {', '.join(active)}")
    return "\n".join(lines)


def _chunks_from_json(
    corpus_root: Path,
    source: ManifestSource,
) -> list[dict[str, Any]]:
    path = _validate_manifest_path(corpus_root, source.path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing public source: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    if source.path == "locations.json":
        locations = data.get("locations")
        if not isinstance(locations, list):
            raise PublicCorpusError(f"{path}: locations must be a list")
        sorted_locs = sorted(
            locations,
            key=lambda loc: str(loc.get("slug", "")),
        )
        chunks: list[dict[str, Any]] = []
        for loc in sorted_locs:
            if not isinstance(loc, dict):
                continue
            slug = str(loc.get("slug", ""))
            text = _format_location_record(loc, source)
            chunks.append(
                _public_payload_base(
                    source,
                    record_id=slug,
                    section=str(loc.get("display_name", slug)),
                    text=text,
                    chunk_index=0,
                )
            )
        return chunks

    if source.path == "menu.json":
        items = data.get("items")
        if not isinstance(items, list):
            raise PublicCorpusError(f"{path}: items must be a list")
        sorted_items = sorted(items, key=lambda item: str(item.get("id", "")))
        chunks = []
        for item in sorted_items:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id", ""))
            text = _format_menu_item(item, source)
            chunks.append(
                _public_payload_base(
                    source,
                    record_id=item_id,
                    section=str(item.get("name", item_id)),
                    text=text,
                    chunk_index=0,
                )
            )
        return chunks

    raise PublicCorpusError(f"unsupported json source: {source.path}")


def _chunks_from_markdown(
    corpus_root: Path,
    source: ManifestSource,
) -> list[dict[str, Any]]:
    path = _validate_manifest_path(corpus_root, source.path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing public source: {path}")
    stem = Path(source.path).stem
    raw_chunks = chunk_markdown(
        path.read_text(encoding="utf-8"),
        source_document=stem,
    )
    return [
        _public_payload_base(
            source,
            record_id=f"{stem}:{chunk['chunk_index']}",
            section=str(chunk["section"]),
            text=str(chunk["text"]),
            chunk_index=int(chunk["chunk_index"]),
        )
        for chunk in raw_chunks
    ]


def build_public_chunks(corpus_root: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Build all public chunks from manifest allowlist only."""
    if not corpus_root.is_dir():
        raise FileNotFoundError(f"Public corpus not found: {corpus_root}")
    sources = load_manifest(corpus_root)
    all_chunks: list[dict[str, Any]] = []
    per_document: dict[str, int] = {}
    for source in sources:
        if source.format == "json":
            chunks = _chunks_from_json(corpus_root, source)
        else:
            chunks = _chunks_from_markdown(corpus_root, source)
        per_document[source.path] = len(chunks)
        all_chunks.extend(chunks)
    return all_chunks, per_document
