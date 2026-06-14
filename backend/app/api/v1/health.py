from typing import Any

from app.config import Settings, get_settings
from app.dependencies import get_db
from app.services.health_service import gather_health
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
async def health_check(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    payload = await gather_health(session, settings)
    if payload["status"] != "healthy":
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)
    return payload
