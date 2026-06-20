from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from incident_analysis import export_summary_csv, run_analysis
from incident_analysis.loader import CsvStructureError
from incident_analysis.types import AnalysisResult

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Brasaland Incident Analysis")

_last_analysis: AnalysisResult | None = None


def _serialize_result(result: AnalysisResult) -> dict[str, Any]:
    return {
        "totals": {
            "total": result.totals.total,
            "valid": result.totals.valid,
            "invalid": result.totals.invalid,
        },
        "by_category": result.by_category,
        "by_status": result.by_status,
        "average_satisfaction_closed": result.average_satisfaction_closed,
        "satisfaction_distribution": result.satisfaction_distribution,
        "invalid_count_by_rule": result.invalid_count_by_rule,
        "invalid_records": [
            {
                "incident_id": record.incident_id,
                "failed_rules": list(record.failed_rules),
            }
            for record in result.invalid_records
        ],
    }


def _map_analysis_error(error: Exception) -> HTTPException:
    if isinstance(error, CsvStructureError):
        message = str(error).lower()
        if "no data rows" in message:
            return HTTPException(status_code=400, detail="The CSV file is empty")
        return HTTPException(status_code=400, detail="Invalid CSV structure")
    if isinstance(error, UnicodeDecodeError):
        return HTTPException(status_code=400, detail="Invalid CSV structure")
    return HTTPException(status_code=400, detail="Invalid CSV structure")


@app.get("/")
async def read_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/incidents/analyze")
async def analyze_incidents(
    file: UploadFile | None = File(default=None),
) -> dict[str, Any]:
    global _last_analysis

    if file is None or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    contents = await file.read()
    if not contents.strip():
        raise HTTPException(status_code=400, detail="The CSV file is empty")

    try:
        text_stream = StringIO(contents.decode("utf-8"))
        result = run_analysis(text_stream)
    except CsvStructureError as error:
        raise _map_analysis_error(error) from error
    except UnicodeDecodeError as error:
        raise _map_analysis_error(error) from error

    _last_analysis = result
    return _serialize_result(result)


@app.get("/api/incidents/results/export")
async def export_results() -> Response:
    if _last_analysis is None:
        raise HTTPException(
            status_code=404,
            detail="No analysis available yet",
        )

    csv_content = export_summary_csv(_last_analysis)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="incident-summary.csv"',
        },
    )


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
