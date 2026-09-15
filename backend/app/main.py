from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app import __version__
from backend.app.api.v1.router import api_router
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="BlueSentra API",
        description=(
            "Agentless network detection & visibility for MSPs. "
            "Under active development — not production-ready."
        ),
        version=__version__,
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
