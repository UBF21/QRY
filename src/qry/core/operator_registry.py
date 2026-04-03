from __future__ import annotations

from typing import Any, Callable, Dict, Iterable

from qry.core.enums import OperatorEnum

OperatorHandler = Callable[[Any, Any], Any]

_HANDLERS: Dict[OperatorEnum, OperatorHandler] = {}


def register_operator_handler(operator: OperatorEnum, handler: OperatorHandler) -> OperatorHandler:
    """Register the handler responsible for building expressions for an operator."""
    _HANDLERS[operator] = handler
    return handler


def register_operator(operator: OperatorEnum) -> Callable[[OperatorHandler], OperatorHandler]:
    """Decorator that registers the wrapped handler for the given operator."""

    def decorator(handler: OperatorHandler) -> OperatorHandler:
        return register_operator_handler(operator, handler)

    return decorator


def get_operator_handler(operator: OperatorEnum) -> OperatorHandler:
    """Return the handler registered for the operator."""
    try:
        return _HANDLERS[operator]
    except KeyError as exc:
        raise ValueError(f"Unsupported operator: {operator}") from exc


def list_registered_operators() -> Iterable[OperatorEnum]:
    """Return the operators that currently have registered handlers."""
    return tuple(_HANDLERS.keys())
