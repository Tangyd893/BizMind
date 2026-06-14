"""Pagination helper — one reusable function for all list endpoints."""

import math
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int


def paginate(items: list, total: int, page: int, page_size: int) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, math.ceil(total / page_size)) if total > 0 else 1,
    }
