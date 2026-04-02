from __future__ import annotations

from typing import Any

from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import InstrumentedAttribute


class JoinManager:
    """Tracks joins and aliases to avoid duplicate SQLAlchemy joins."""

    def __init__(self, joined_models: list[Any] | None = None) -> None:
        self._joined_models: list[str] = []
        self._joined_relation_fields: dict[tuple[str, str], list[str]] = {}

        for model in joined_models or []:
            self._joined_models.append(self._table_key(model))

    def reset(self, joined_models: list[Any] | None = None) -> None:
        self._joined_models = []
        self._joined_relation_fields = {}
        for model in joined_models or []:
            self._joined_models.append(self._table_key(model))

    def ensure_join(
        self,
        query: Any,
        root_model: Any,
        target: Any,
        *,
        isouter: bool = False,
    ) -> tuple[Any, Any]:
        if isinstance(target, InstrumentedAttribute):
            return self._join_relationship(query=query, relationship=target, isouter=isouter)

        if isinstance(target, (tuple, list)):
            return self._join_legacy_path(
                query=query,
                root_model=root_model,
                target=target,
                isouter=isouter,
            )

        table_key = self._table_key(target)
        if table_key not in self._joined_models:
            query = query.join(target, isouter=isouter)
            self._joined_models.append(table_key)

        return query, target

    def _join_relationship(
        self,
        *,
        query: Any,
        relationship: InstrumentedAttribute,
        isouter: bool,
    ) -> tuple[Any, Any]:
        model_class = relationship.property.mapper.class_
        table_key = self._table_key(model_class)
        base_table = relationship.class_.__name__
        relation_key = relationship.property.key

        if (base_table, table_key) not in self._joined_relation_fields:
            self._joined_relation_fields[(base_table, table_key)] = [relation_key]

        if table_key not in self._joined_models:
            query = query.join(relationship, isouter=isouter)
            self._joined_models.append(table_key)
            return query, relationship

        known_relations = self._joined_relation_fields[(base_table, table_key)]
        if relation_key in known_relations:
            return query, relationship

        model_alias = aliased(model_class, name=f"{table_key}_{relation_key}")
        known_relations.append(relation_key)
        query = query.join(relationship.of_type(model_alias), isouter=isouter)
        return query, relationship.of_type(model_alias)

    def _join_legacy_path(
        self,
        *,
        query: Any,
        root_model: Any,
        target: tuple[Any, ...] | list[Any],
        isouter: bool,
    ) -> tuple[Any, Any]:
        base_model = root_model
        current_model = root_model

        for step in target:
            if not isinstance(step, tuple) or not step:
                query, current_model = self.ensure_join(
                    query=query,
                    root_model=base_model,
                    target=step,
                    isouter=isouter,
                )
                base_model = getattr(current_model, "property", None) or current_model
                continue

            model_class = step[0]
            table_key = self._table_key(model_class)
            if table_key not in self._joined_models:
                if len(step) == 1:
                    query = query.join(model_class, isouter=isouter)
                elif len(step) == 2:
                    query = query.join(
                        model_class,
                        getattr(model_class, "id") == getattr(base_model, step[1]),
                        isouter=isouter,
                    )
                else:
                    query = query.join(
                        model_class,
                        getattr(model_class, step[2]) == getattr(base_model, step[1]),
                        isouter=isouter,
                    )
                self._joined_models.append(table_key)

            current_model = model_class
            base_model = model_class

        return query, current_model

    @staticmethod
    def _table_key(model: Any) -> str:
        if isinstance(model, str):
            return model.lower()
        if hasattr(model, "__table__"):
            return str(model.__table__.name)
        return getattr(model, "name", model.__class__.__name__).lower()

