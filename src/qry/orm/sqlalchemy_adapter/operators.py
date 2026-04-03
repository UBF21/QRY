from __future__ import annotations

from typing import Any

from qry.core.enums import OperatorEnum
from qry.core.operator_registry import get_operator_handler, register_operator
from qry.core.parsing import format_like_value


@register_operator(OperatorEnum.EQ)
def _eq(column: Any, value: Any) -> Any:
    return column == value


@register_operator(OperatorEnum.NEQ)
def _neq(column: Any, value: Any) -> Any:
    return column != value


@register_operator(OperatorEnum.GT)
def _gt(column: Any, value: Any) -> Any:
    return column > value


@register_operator(OperatorEnum.GTE)
def _gte(column: Any, value: Any) -> Any:
    return column >= value


@register_operator(OperatorEnum.IN)
def _in(column: Any, value: Any) -> Any:
    return column.in_(value)


@register_operator(OperatorEnum.NOT_IN)
def _not_in(column: Any, value: Any) -> Any:
    return column.not_in(value)


@register_operator(OperatorEnum.IS_NULL)
def _is_null(column: Any, value: Any) -> Any:
    return column.is_(None) if value is True else column.is_not(None)


@register_operator(OperatorEnum.LT)
def _lt(column: Any, value: Any) -> Any:
    return column < value


@register_operator(OperatorEnum.LTE)
def _lte(column: Any, value: Any) -> Any:
    return column <= value


@register_operator(OperatorEnum.LIKE)
def _like(column: Any, value: Any) -> Any:
    return column.like(format_like_value(value))


@register_operator(OperatorEnum.ILIKE)
def _ilike(column: Any, value: Any) -> Any:
    return column.ilike(format_like_value(value))


@register_operator(OperatorEnum.NOT)
def _not(column: Any, value: Any) -> Any:
    return column.is_not(value)


@register_operator(OperatorEnum.BETWEEN)
def _between(column: Any, value: Any) -> Any:
    low, high = value
    return column.between(low, high)


def build_expression(column: Any, operator: OperatorEnum, value: Any) -> Any:
    handler = get_operator_handler(operator)
    return handler(column, value)
