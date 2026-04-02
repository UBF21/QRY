from __future__ import annotations

import math
from typing import Any

from sqlalchemy import asc, desc
from sqlalchemy.orm import contains_eager
from sqlalchemy.sql.expression import Select, Update

from qry.core.schemas import (
    FilterSchema,
    HavingFilterSchema,
    PaginationSchema,
    RelationFilterSchema,
    ResolvedOrderBySchema,
)
from qry.orm.base.adapter import BaseQueryAdapter
from qry.orm.sqlalchemy_adapter.join_manager import JoinManager
from qry.orm.sqlalchemy_adapter.operators import build_expression


class SQLAlchemyQueryAdapter(BaseQueryAdapter[Select | Update]):
    """Apply qry schemas to SQLAlchemy 2.x statements."""

    def __init__(self, joined_models: list[Any] | None = None) -> None:
        self._join_manager = JoinManager(joined_models=joined_models)

    def reset(self, joined_models: list[Any] | None = None) -> None:
        self._join_manager.reset(joined_models=joined_models)

    def build(
        self,
        *,
        query: Select | Update,
        model: Any,
        filters: list[FilterSchema] | None = None,
        relation_filters: list[RelationFilterSchema] | None = None,
        order_by: list[ResolvedOrderBySchema] | None = None,
        having_filters: list[HavingFilterSchema] | None = None,
        pagination: PaginationSchema | None = None,
        load_relations: list[str] | None = None,
        load_sub_relations: list[tuple[str, tuple[Any, str]]] | None = None,
    ) -> Select | Update:
        query = self._apply_filters(query=query, model=model, filters=filters or [])
        query = self._apply_relation_filters(
            query=query,
            model=model,
            relation_filters=relation_filters or [],
        )
        query = self._apply_having(query=query, having_filters=having_filters or [])
        query = self._load_relations(
            query=query,
            model=model,
            load_relations=load_relations or [],
        )
        query = self._load_sub_relations(
            query=query,
            model=model,
            load_sub_relations=load_sub_relations or [],
        )

        if isinstance(query, Select):
            query = self._apply_order_by(query=query, model=model, order_by=order_by or [])

        if pagination and pagination.page_size > 0:
            query = self._apply_pagination(query=query, pagination=pagination)

        return query

    def calculate_num_pages(self, total_results: int, pagination: PaginationSchema) -> int:
        if pagination.page_size == 0:
            return 1
        return math.ceil(float(total_results) / float(pagination.page_size))

    def _apply_filters(
        self,
        *,
        query: Select | Update,
        model: Any,
        filters: list[FilterSchema],
    ) -> Select | Update:
        for item in filters:
            model_field = getattr(model, item.column)
            query = query.filter(build_expression(model_field, item.operator, item.value))
        return query

    def _apply_relation_filters(
        self,
        *,
        query: Select | Update,
        model: Any,
        relation_filters: list[RelationFilterSchema],
    ) -> Select | Update:
        for item in relation_filters:
            query, joined_target = self._join_manager.ensure_join(
                query=query,
                root_model=model,
                target=item.target,
            )
            model_ref = self._resolve_model_reference(joined_target, fallback=item.target)
            model_field = getattr(model_ref, item.column)
            query = query.filter(build_expression(model_field, item.operator, item.value))
        return query

    def _apply_having(
        self,
        *,
        query: Select | Update,
        having_filters: list[HavingFilterSchema],
    ) -> Select | Update:
        for item in having_filters:
            query = query.having(build_expression(item.func, item.operator, item.value))
        return query

    def _apply_order_by(
        self,
        *,
        query: Select,
        model: Any,
        order_by: list[ResolvedOrderBySchema],
    ) -> Select:
        for item in order_by:
            try:
                if item.target is not None:
                    query, joined_target = self._join_manager.ensure_join(
                        query=query,
                        root_model=model,
                        target=item.target,
                    )
                    model_ref = self._resolve_model_reference(joined_target, fallback=item.target)
                    order_column = getattr(model_ref, item.column)
                else:
                    order_column = getattr(model, item.column)

                query = query.order_by(getattr(order_column, item.direction.value)())
            except AttributeError:
                query = query.order_by(asc(item.column) if item.direction.value == "asc" else desc(item.column))

        return query

    def _apply_pagination(self, *, query: Select | Update, pagination: PaginationSchema) -> Select | Update:
        query = query.limit(pagination.page_size)
        query = query.offset((pagination.page_number - 1) * pagination.page_size)
        return query

    def _load_relations(
        self,
        *,
        query: Select | Update,
        model: Any,
        load_relations: list[str],
    ) -> Select | Update:
        for relation_name in load_relations:
            relation = getattr(model, relation_name)
            query, relation_ref = self._join_manager.ensure_join(
                query=query,
                root_model=model,
                target=relation,
                isouter=True,
            )
            query = query.options(contains_eager(relation_ref))

        return query

    def _load_sub_relations(
        self,
        *,
        query: Select | Update,
        model: Any,
        load_sub_relations: list[tuple[str, tuple[Any, str]]],
    ) -> Select | Update:
        for relation_name, sub_relation in load_sub_relations:
            relation = getattr(model, relation_name)
            query, relation_ref = self._join_manager.ensure_join(
                query=query,
                root_model=model,
                target=relation,
                isouter=True,
            )
            query = query.options(contains_eager(relation_ref).subqueryload(getattr(sub_relation[0], sub_relation[1])))

        return query

    @staticmethod
    def _resolve_model_reference(joined_target: Any, fallback: Any) -> Any:
        if hasattr(joined_target, "property") and hasattr(joined_target.property, "mapper"):
            return joined_target.property.mapper.class_
        if isinstance(fallback, (tuple, list)) and fallback:
            last_step = fallback[-1]
            if isinstance(last_step, tuple) and last_step:
                return last_step[0]
        return joined_target

