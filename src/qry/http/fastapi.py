from __future__ import annotations

from typing import Any

from fastapi import Query

from qry.compat.pydantic import BaseModel, ConfigDict, Field, PYDANTIC_V1, model_dump
from qry.core.enums import OperatorEnum
from qry.core.parsing import parse_filter_key, parse_order_by_string
from qry.core.schemas import (
    FilterSchema,
    HavingFilterSchema,
    PaginationSchema,
    RelationFilterSchema,
    ResolvedOrderBySchema,
)


class CoreFilter(BaseModel):
    """Base filter contract for FastAPI endpoints."""

    order_by: str | None = Field(
        Query(
            default=None,
            description=(
                "Fields separated by comma. Use '-' for DESC and '+' for ASC. "
                "Example: '-created_at,+email'."
            ),
        )
    )
    page_number: int = Field(Query(default=1, ge=1))
    page_size: int = Field(Query(default=10, ge=0))

    class FilterConfig:
        relation_filters: dict[str, Any] = {}
        relation_order_by: dict[str, Any] = {}
        having_filters: dict[str, Any] = {}
        allowed_ordering_fields: list[str] | None = None
        reject_invalid_ordering_fields: bool = False

    if PYDANTIC_V1:
        class Config:
            extra = "forbid"
    else:
        model_config = ConfigDict(extra="forbid")

    @property
    def filtering_fields(self) -> dict[str, Any]:
        """Backward-compatible raw dictionary of model filters."""
        reserved = {"order_by", "page_number", "page_size"}
        reserved.update(getattr(self.FilterConfig, "relation_filters", {}).keys())
        reserved.update(getattr(self.FilterConfig, "having_filters", {}).keys())

        return model_dump(
            self,
            exclude_none=True,
            exclude_unset=True,
            exclude=reserved,
        )

    @property
    def model_filters(self) -> list[FilterSchema]:
        """Structured model filters ready for adapters."""
        result: list[FilterSchema] = []

        for field_name, value in self.filtering_fields.items():
            column, operator = parse_filter_key(field_name)
            if operator == OperatorEnum.EQ and isinstance(value, list):
                operator = OperatorEnum.IN
            result.append(FilterSchema(column=column, operator=operator, value=value))

        return result

    @property
    def relation_filtering_fields(self) -> list[RelationFilterSchema]:
        result: list[RelationFilterSchema] = []
        relation_filters = getattr(self.FilterConfig, "relation_filters", {})

        for filter_field_name, target in relation_filters.items():
            value = getattr(self, filter_field_name, None)
            if value is None:
                continue

            column, operator = parse_filter_key(filter_field_name)
            resolved_column = self._resolve_relation_column(default_column=column, target=target)
            result.append(
                RelationFilterSchema(
                    column=resolved_column,
                    operator=operator,
                    value=value,
                    target=target,
                )
            )

        return result

    @property
    def having_filtering_fields(self) -> list[HavingFilterSchema]:
        result: list[HavingFilterSchema] = []
        configured = getattr(self.FilterConfig, "having_filters", {})

        for filter_field, func in configured.items():
            value = getattr(self, filter_field, None)
            if value is None:
                continue

            column, operator = parse_filter_key(filter_field)
            result.append(
                HavingFilterSchema(
                    column=column,
                    func=func,
                    value=value,
                    operator=operator,
                )
            )

        return result

    @property
    def ordering_fields(self) -> list[ResolvedOrderBySchema]:
        allowed_fields = getattr(self.FilterConfig, "allowed_ordering_fields", None)
        configured_relations = getattr(self.FilterConfig, "relation_order_by", {})
        reject_invalid_ordering = getattr(
            self.FilterConfig,
            "reject_invalid_ordering_fields",
            False,
        )
        parsed_fields = parse_order_by_string(
            self.order_by,
            allowed_fields=allowed_fields,
            raise_on_invalid=reject_invalid_ordering and allowed_fields is not None,
        )
        resolved: list[ResolvedOrderBySchema] = []

        for item in parsed_fields:
            target = None
            column = item.column

            if item.column in configured_relations:
                mapped = configured_relations[item.column]
                if isinstance(mapped, tuple) and len(mapped) == 2 and isinstance(mapped[0], str):
                    column = mapped[0]
                    target = mapped[1]
                else:
                    target = mapped

            resolved.append(
                ResolvedOrderBySchema(
                    column=column,
                    direction=item.direction,
                    target=target,
                )
            )

        return resolved

    @property
    def pagination(self) -> PaginationSchema:
        return PaginationSchema(page_number=self.page_number, page_size=self.page_size)

    @staticmethod
    def _resolve_relation_column(default_column: str, target: Any) -> str:
        """Support direct relation targets and legacy tuple/list join chains."""
        if isinstance(target, list) and len(target) == 1 and isinstance(target[0], tuple):
            return default_column

        if isinstance(target, tuple) and target:
            last_step = target[-1]
            if isinstance(last_step, tuple) and len(last_step) >= 2:
                return last_step[1]

        return default_column
