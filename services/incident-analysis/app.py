from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from io import StringIO
from pathlib import Path
from typing import Annotated, Any

from brasaland_auth_verify.deps import get_verified_claims
from brasaland_auth_verify.verify import ensure_jwt_configured
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from incident_analysis import export_summary_csv, run_analysis
from incident_analysis.loader import CsvStructureError
from incident_analysis.types import AnalysisResult
from result_store import result_store

STATIC_DIR = Path(__file__).parent / "static"

RESULT_NOT_FOUND = "Analysis result not found"
NOT_ALLOWED_TO_EXPORT = "Not allowed to export this analysis result"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_jwt_configured()
    yield


app = FastAPI(title="Brasaland Incident Analysis", lifespan=lifespan)


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


def _caller_identity(claims: dict[str, Any]) -> tuple[str, bool]:
    user_id = claims.get("user_id", claims.get("sub"))
    if user_id is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return str(user_id), bool(claims.get("is_admin"))


@app.get("/")
async def read_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/incidents/analyze")
async def analyze_incidents(
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
    file: UploadFile | None = File(default=None),
) -> dict[str, Any]:
    owner_uuid, _is_admin = _caller_identity(claims)

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
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Analysis failed",
        ) from error

    stored = result_store.store(owner_uuid, result)
    payload = _serialize_result(result)
    payload["result_id"] = stored.result_id
    return payload


@app.get("/api/incidents/results/{result_id}/export")
async def export_results(
    result_id: str,
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> Response:
    requester_uuid, is_admin = _caller_identity(claims)
    stored = result_store.get(result_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=RESULT_NOT_FOUND)

    if stored.owner_user_uuid != requester_uuid and not is_admin:
        raise HTTPException(status_code=403, detail=NOT_ALLOWED_TO_EXPORT)

    csv_content = export_summary_csv(stored.result)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="incident-summary.csv"',
        },
    )


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
