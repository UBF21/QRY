from __future__ import annotations

from typing import Any

from qry.core.enums import OperatorEnum
from qry.core.parsing import format_like_value


def build_expression(column: Any, operator: OperatorEnum, value: Any) -> Any:
    """Build a SQLAlchemy boolean expression from a structured filter."""
    if operator == OperatorEnum.EQ:
        return column == value
    if operator == OperatorEnum.NEQ:
        return column != value
    if operator == OperatorEnum.GT:
        return column > value
    if operator == OperatorEnum.GTE:
        return column >= value
    if operator == OperatorEnum.IN:
        return column.in_(value)
    if operator == OperatorEnum.NOT_IN:
        return column.not_in(value)
    if operator == OperatorEnum.IS_NULL:
        return column.is_(None) if value is True else column.is_not(None)
    if operator == OperatorEnum.LT:
        return column < value
    if operator == OperatorEnum.LTE:
        return column <= value
    if operator == OperatorEnum.LIKE:
        return column.like(format_like_value(value))
    if operator == OperatorEnum.ILIKE:
        return column.ilike(format_like_value(value))
    if operator == OperatorEnum.NOT:
        return column.is_not(value)
    if operator == OperatorEnum.BETWEEN:
        low, high = value
        return column.between(low, high)

    raise ValueError(f"Unsupported operator: {operator}")

