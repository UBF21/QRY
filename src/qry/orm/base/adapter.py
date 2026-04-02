from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from qry.core.schemas import (
    FilterSchema,
    HavingFilterSchema,
    PaginationSchema,
    RelationFilterSchema,
    ResolvedOrderBySchema,
)

QueryT = TypeVar("QueryT")


class BaseQueryAdapter(ABC, Generic[QueryT]):
    """Abstract contract for ORM-specific query adapters."""

    @abstractmethod
    def build(
        self,
        *,
        query: QueryT,
        model: Any,
        filters: list[FilterSchema] | None = None,
        relation_filters: list[RelationFilterSchema] | None = None,
        order_by: list[ResolvedOrderBySchema] | None = None,
        having_filters: list[HavingFilterSchema] | None = None,
        pagination: PaginationSchema | None = None,
        **kwargs: Any,
    ) -> QueryT:
        """Return a query with filters, order and pagination applied."""

