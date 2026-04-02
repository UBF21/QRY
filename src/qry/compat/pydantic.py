"""Pydantic v1/v2 compatibility helpers."""

from __future__ import annotations

from typing import Any

try:
    from pydantic.v1 import BaseModel
    from pydantic.v1 import Field as _Field

    PYDANTIC_V1 = True
    ConfigDict = None
    Field = _Field
except ImportError:  # pragma: no cover - exercised when only v2 is installed.
    from pydantic import BaseModel
    from pydantic import ConfigDict as _ConfigDict
    from pydantic import Field as _Field

    PYDANTIC_V1 = False
    ConfigDict = _ConfigDict
    Field = _Field


def model_dump(instance: BaseModel, **kwargs: Any) -> dict[str, Any]:
    """Normalize model export across Pydantic versions."""
    if hasattr(instance, "model_dump"):
        return instance.model_dump(**kwargs)
    return instance.dict(**kwargs)
