"""Fixed RAG profile definitions for staff and public knowledge paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ProfileName = Literal["staff", "public"]

PROFILE_ALLOWLIST = frozenset({"staff", "public"})

STAFF_SOURCE_STEMS = (
    "loyalty-program",
    "waste-protocol",
    "menu-allergens",
    "supplier-ordering",
)

PUBLIC_NO_CONTEXT_ANSWER = (
    "I don't have verified public information for that yet. "
    "Please ask a team member or check our website."
)


@dataclass(frozen=True, slots=True)
class RagProfile:
    name: ProfileName
    collection_name: str
    corpus_relpath: str
    audience: str | None
    locale: str
    min_score: float
    top_k: int
    vector_size: int
    generation_max_tokens: int | None
    generation_temperature: float
    max_generation_fallbacks: int | None
    no_context_answer: str | None


STAFF_PROFILE = RagProfile(
    name="staff",
    collection_name="brasaland_knowledge",
    corpus_relpath="docs/company-knowledge-base",
    audience=None,
    locale="en",
    min_score=0.55,
    top_k=5,
    vector_size=384,
    generation_max_tokens=None,
    generation_temperature=0.2,
    max_generation_fallbacks=None,
    no_context_answer=None,
)

PUBLIC_PROFILE = RagProfile(
    name="public",
    collection_name="brasaland_knowledge_public",
    corpus_relpath="docs/public-knowledge-base",
    audience="public",
    locale="en",
    min_score=0.45,
    top_k=5,
    vector_size=384,
    generation_max_tokens=512,
    generation_temperature=0.1,
    max_generation_fallbacks=1,
    no_context_answer=PUBLIC_NO_CONTEXT_ANSWER,
)


def resolve_profile(profile: RagProfile | ProfileName | None = None) -> RagProfile:
    """Resolve a profile name or instance; default is staff."""
    if profile is None:
        return STAFF_PROFILE
    if isinstance(profile, RagProfile):
        if profile.name not in PROFILE_ALLOWLIST:
            raise ValueError(f"invalid profile: {profile.name!r}")
        return profile
    name = str(profile).strip().lower()
    if name not in PROFILE_ALLOWLIST:
        raise ValueError(
            f"invalid profile: {profile!r}; allowed: {sorted(PROFILE_ALLOWLIST)}"
        )
    if name == "public":
        return PUBLIC_PROFILE
    return STAFF_PROFILE
