from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.core.exceptions import AppException, app_exception_handler
from app.core.logging import RequestContextMiddleware, configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="BizMind API",
        version="0.1.0",
        description="Enterprise knowledge assistant — multi-tenant Agentic RAG platform",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_debug or settings.app_env != "production" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(AppException, app_exception_handler)
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
