"""Shared schema pieces: pagination envelope, error envelope."""
from typing import Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """README / ARCH §6: ``{ "items": [...], "total": n, "page": 1, "page_size": 20 }``."""

    items: list[T]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    """Documents the uniform error body in OpenAPI (422 may carry a list of messages)."""

    detail: str | list[str]


class PaginationParams:
    """Dependency: ``?page=1&page_size=20`` (max 100)."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="1-based page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def paginate(items: list[Any], total: int, params: PaginationParams) -> dict[str, Any]:
    """Build the page envelope; FastAPI validates it against ``Page[Schema]``."""
    return {"items": items, "total": total, "page": params.page, "page_size": params.page_size}
