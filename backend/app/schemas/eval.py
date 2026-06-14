from datetime import datetime

from pydantic import BaseModel


class EvalRunRequest(BaseModel):
    mode: str = "baseline"  # baseline, agent, or both
    dataset: str = "default"
    sample_limit: int | None = None


class EvalRunResponse(BaseModel):
    id: str
    tenant_id: str
    triggered_by: str | None = None
    mode: str
    dataset_path: str
    sample_count: int
    metrics: dict
    config_snapshot: dict
    duration_sec: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
