"""Hardened multipart PDF upload for RFP intake.

Defenses:
- Size cap (MAX_UPLOAD_BYTES): reject oversized bodies with 413 before writing.
- Magic-byte check: require ``%PDF-`` prefix so non-PDFs never land on disk as .pdf.
- Server-side uuid filename: client ``filename`` is never used in the path (traversal).
- Path traversal: writes only under DATA_RAW with a generated ``{uuid}.pdf`` name.
- Streaming: chunks stream to DATA_RAW/.tmp (same volume as finals) — never /tmp.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from config import DATA_ROOT

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
_CHUNK_SIZE = 1024 * 1024
_PDF_MAGIC = b"%PDF-"

DATA_RAW = DATA_ROOT / "raw"


def _data_raw_tmp() -> Path:
    return DATA_RAW / ".tmp"


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        logger.warning("failed to unlink upload path %s: %s", path, exc)


async def save_upload_to_temp(file: UploadFile) -> tuple[Path, str]:
    """Stream upload to DATA_RAW/.tmp/{uuid}.part; return (temp_path, sha256 hex)."""
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    data_raw_tmp = _data_raw_tmp()
    data_raw_tmp.mkdir(parents=True, exist_ok=True)

    temp_path = data_raw_tmp / f"{uuid4().hex}.part"
    hasher = hashlib.sha256()
    total = 0
    header_checked = False

    try:
        with temp_path.open("wb") as out:
            while True:
                chunk = await file.read(_CHUNK_SIZE)
                if not chunk:
                    break
                if not header_checked:
                    if not chunk.startswith(_PDF_MAGIC):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="uploaded file is not a valid PDF",
                        )
                    header_checked = True
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="uploaded file exceeds 10 MiB limit",
                    )
                hasher.update(chunk)
                out.write(chunk)

        if total == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="uploaded file is not a valid PDF",
            )

        return temp_path, hasher.hexdigest()
    except HTTPException:
        _safe_unlink(temp_path)
        raise
    except Exception:
        _safe_unlink(temp_path)
        raise
