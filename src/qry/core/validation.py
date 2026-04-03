from __future__ import annotations

from collections.abc import Collection
from typing import Iterable

from qry.core.enums import OperatorEnum
from qry.core.operator_registry import get_operator_handler
from qry.core.parsing import OrderBySchema, parse_order_by_string


def ensure_operator_registered(operator: OperatorEnum) -> None:
    """Ensure the OperatorEnum has a registered handler."""
    get_operator_handler(operator)


def resolve_ordering_fields(
    raw_order_by: str | None,
    allowed_fields: Collection[str] | None,
    reject_invalid: bool,
) -> list[OrderBySchema]:
    """Parse and optionally enforce ordering allowlist."""
    if not raw_order_by:
        return []

    raise_on_invalid = reject_invalid and allowed_fields is not None
    return parse_order_by_string(
        raw_order_by,
        allowed_fields=allowed_fields,
        raise_on_invalid=raise_on_invalid,
    )


def list_allowed_ordering_fields(allowed_fields: Collection[str] | None) -> Iterable[str]:
    """Utility helper used by logging/tests to inspect enabled fields."""
    return tuple(allowed_fields or ())
