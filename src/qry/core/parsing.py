from __future__ import annotations

from collections.abc import Collection

from qry.core.enums import OperatorEnum, OrderDirectionEnum
from qry.core.schemas import OrderBySchema


def format_like_value(value: str) -> str:
    """Wrap a string with SQL wildcard markers if missing."""
    if not value.startswith("%"):
        value = f"%{value}"
    if not value.endswith("%"):
        value = f"{value}%"
    return value


def parse_filter_key(field_name: str) -> tuple[str, OperatorEnum]:
    """Parse `field__operator` into `(field, operator)`."""
    if "__" not in field_name:
        return field_name, OperatorEnum.EQ

    column, raw_operator = field_name.rsplit("__", 1)
    return column, OperatorEnum(raw_operator)


def parse_order_by_string(
    value: str | None,
    allowed_fields: Collection[str] | None = None,
) -> list[OrderBySchema]:
    """Parse `-field,+other_field` strings into structured order definitions."""
    if not value:
        return []

    result: list[OrderBySchema] = []

    for raw_item in value.split(","):
        item = raw_item.strip()
        if not item:
            continue

        direction = OrderDirectionEnum.ASC
        if item.startswith("-"):
            direction = OrderDirectionEnum.DESC
            item = item[1:]
        elif item.startswith("+"):
            item = item[1:]

        if not item:
            continue

        if allowed_fields is not None and item not in allowed_fields:
            continue

        result.append(OrderBySchema(column=item, direction=direction))

    return result

