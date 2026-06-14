from datetime import datetime

from pydantic import BaseModel


class CreateThreadRequest(BaseModel):
    title: str | None = None


class ThreadResponse(BaseModel):
    id: str
    title: str | None = None
    documents_version: int
    is_stale: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    source: str
    page: int | None = None
    text_preview: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: list[Citation] = []
    token_usage: dict | None = None
    latency_ms: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ThreadMessagesResponse(BaseModel):
    thread_id: str
    is_stale: bool
    documents_version: int
    messages: list[MessageResponse]
