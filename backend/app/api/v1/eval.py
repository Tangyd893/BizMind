"""Eval routes — benchmarking endpoints (admin only)."""

from app.core.pagination import paginate
from app.dependencies import get_current_admin, get_db
from app.models import User
from app.schemas.eval import EvalRunRequest
from app.services.eval_service import get_eval_run, list_eval_runs, run_eval
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/eval", tags=["eval"])


@router.post("/run", status_code=202)
async def start_eval(
    req: EvalRunRequest,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> dict:
    """Start an evaluation run. Returns run_id for status polling."""
    return await run_eval(
        session, admin, req.mode, dataset_name=req.dataset, sample_limit=req.sample_limit
    )


@router.get("/results")
async def list_results(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> dict:
    """List evaluation runs for the admin's tenant."""
    items, total = await list_eval_runs(
        session, tenant_id=str(admin.tenant_id), page=page, page_size=page_size
    )
    return paginate(items, total, page, page_size)


@router.get("/results/{run_id}")
async def get_result(
    run_id: str,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> dict:
    """Get a single evaluation run detail."""
    run = await get_eval_run(session, run_id, tenant_id=str(admin.tenant_id))
    if run is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Eval run not found")
    return run
