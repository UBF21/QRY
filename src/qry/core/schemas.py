from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qry.core.enums import OperatorEnum, OrderDirectionEnum


@dataclass(slots=True, frozen=True, kw_only=True)
class FilterSchema:
    column: str
    operator: OperatorEnum = OperatorEnum.EQ
    value: Any = None


@dataclass(slots=True, frozen=True, kw_only=True)
class RelationFilterSchema(FilterSchema):
    target: Any


@dataclass(slots=True, frozen=True, kw_only=True)
class HavingFilterSchema:
    column: str
    func: Any
    value: Any
    operator: OperatorEnum = OperatorEnum.EQ


@dataclass(slots=True, frozen=True, kw_only=True)
class OrderBySchema:
    column: str
    direction: OrderDirectionEnum = OrderDirectionEnum.ASC


@dataclass(slots=True, frozen=True, kw_only=True)
class ResolvedOrderBySchema(OrderBySchema):
    target: Any | None = None


@dataclass(slots=True, frozen=True, kw_only=True)
class PaginationSchema:
    page_number: int = 1
    page_size: int = 10

