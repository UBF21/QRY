from __future__ import annotations

from enum import Enum


class OperatorEnum(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    LT = "lt"
    LTE = "lte"
    LIKE = "like"
    ILIKE = "ilike"
    NOT = "not"
    BETWEEN = "between"
    REGEX = "regex"


class OperationEnum(str, Enum):
    AND = "_and"
    OR = "_or"


class OrderDirectionEnum(str, Enum):
    ASC = "asc"
    DESC = "desc"
