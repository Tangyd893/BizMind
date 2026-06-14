from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    status: str
    chunk_count: int = 0
    documents_version: int = 0
    error_message: str | None = None
    created_at: datetime
    indexed_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    pages: int
