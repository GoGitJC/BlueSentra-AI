from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app import __version__
from backend.app.core.config import get_settings
from backend.app.database.session import check_database_connection
from backend.app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="bluesentra-api",
        version=__version__,
        environment=settings.bluesentra_env,
    )


@router.get("/ready", response_model=ReadinessResponse)
def ready():
    db_ok = check_database_connection()
    body = ReadinessResponse(
        status="ready" if db_ok else "degraded",
        database="connected" if db_ok else "unavailable",
    )
    if not db_ok:
        return JSONResponse(status_code=503, content=body.model_dump())
    return body
