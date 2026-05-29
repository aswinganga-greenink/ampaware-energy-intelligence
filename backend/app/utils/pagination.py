"""
app/utils/pagination.py
========================
Typed pagination helpers used across all list endpoints.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field, model_validator

from app.core.config import get_settings

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query-parameter model for paginated endpoints."""

    page: int = Field(default=1, ge=1, description="1-indexed page number")
    page_size: int = Field(default=50, ge=1, description="Records per page")

    @model_validator(mode="after")
    def clamp_page_size(self) -> "PaginationParams":
        max_ps = get_settings().max_page_size
        if self.page_size > max_ps:
            self.page_size = max_ps
        return self

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class Page(BaseModel, Generic[T]):
    """Generic paginated response envelope."""

    items: list[T]
    total: int = Field(description="Total matching records (across all pages)")
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls, items: list[T], total: int, params: PaginationParams
    ) -> "Page[T]":
        total_pages = max(1, -(-total // params.page_size))  # ceiling division
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )
