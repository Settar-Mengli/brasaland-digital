# /// script
# requires-python = ">=3.11"
# dependencies = ["markdown", "xhtml2pdf"]
# ///
"""Render the M9 seed RFP markdown sources to committed PDF fixtures.

Reads each .md in data/raw/seed/ and writes a sibling .pdf.
Run from the repo root:  uv run scripts/render_seed_pdfs.py
"""
from pathlib import Path

import markdown
from xhtml2pdf import pisa

SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "seed"


def render(md_path: Path) -> Path:
    html_body = markdown.markdown(md_path.read_text(encoding="utf-8"))
    html = f"<html><body>{html_body}</body></html>"
    pdf_path = md_path.with_suffix(".pdf")
    with pdf_path.open("wb") as handle:
        result = pisa.CreatePDF(html, dest=handle)
    if result.err:
        raise RuntimeError(f"failed to render {md_path.name}")
    return pdf_path


def main() -> None:
    md_files = sorted(SEED_DIR.glob("*.md"))
    if not md_files:
        raise SystemExit(f"no markdown sources in {SEED_DIR}")
    for md_file in md_files:
        out = render(md_file)
        print(f"rendered {md_file.name} -> {out.name}")


if __name__ == "__main__":
    main()
