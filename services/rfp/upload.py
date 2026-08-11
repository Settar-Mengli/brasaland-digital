"""Hardened multipart PDF upload for RFP intake.

Defenses:
- Size cap (MAX_UPLOAD_BYTES): reject oversized bodies with 413 before writing.
- Magic-byte check: require ``%PDF-`` prefix so non-PDFs never land on disk as .pdf.
- Server-side uuid filename: client ``filename`` is never used in the path (traversal).
- Path traversal: writes only under DATA_RAW with a generated ``{uuid}.pdf`` name.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from config import DATA_ROOT

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
_CHUNK_SIZE = 1024 * 1024
_PDF_MAGIC = b"%PDF-"

DATA_RAW = DATA_ROOT / "raw"


async def save_upload(file: UploadFile) -> tuple[Path, str]:
    """Read upload in chunks; return (written path, sha256 hex digest)."""
    hasher = hashlib.sha256()
    chunks: list[bytes] = []
    total = 0

    while True:
        chunk = await file.read(_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="uploaded file exceeds 10 MiB limit",
            )
        hasher.update(chunk)
        chunks.append(chunk)

    payload = b"".join(chunks)
    if not payload.startswith(_PDF_MAGIC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="uploaded file is not a valid PDF",
        )

    DATA_RAW.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.pdf"
    dest = DATA_RAW / filename
    dest.write_bytes(payload)
    return dest, hasher.hexdigest()
