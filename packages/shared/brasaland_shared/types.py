from dataclasses import dataclass
from typing import TypedDict


class FieldError(TypedDict):
    field: str
    message: str


@dataclass(frozen=True)
class TransitionResult:
    is_allowed: bool
    message: str | None
