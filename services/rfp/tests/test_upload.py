"""Unit tests for streaming PDF upload to DATA_RAW/.tmp."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import upload as upload_module
from upload import save_upload_to_temp


def _tiny_pdf() -> bytes:
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def test_save_upload_to_temp_streams_without_join(tmp_path: Path) -> None:
    payload = _tiny_pdf()
    mid = len(payload) // 2
    chunks = [payload[:mid], payload[mid:], b""]
    raw = tmp_path / "raw"

    upload_file = MagicMock()
    upload_file.read = AsyncMock(side_effect=chunks)

    upload_module.DATA_RAW = raw
    try:
        temp_path, digest = asyncio.run(save_upload_to_temp(upload_file))
    finally:
        upload_module.DATA_RAW = upload_module.DATA_ROOT / "raw"

    assert temp_path.is_file()
    assert temp_path.parent == raw / ".tmp"
    assert temp_path.read_bytes() == payload
    assert digest == hashlib.sha256(payload).hexdigest()
    assert upload_file.read.await_count == 3
