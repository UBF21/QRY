from qry import (
    FilterSchema,
    HavingFilterSchema,
    OperationEnum,
    OperatorEnum,
    OrderBySchema,
    OrderDirectionEnum,
    PaginationSchema,
    RelationFilterSchema,
    ResolvedOrderBySchema,
    format_like_value,
    parse_filter_key,
    parse_order_by_string,
)
from qry.http import CoreFilter
from qry.orm.base import BaseQueryAdapter
from qry.orm.sqlalchemy import SQLAlchemyQueryAdapter


def test_top_level_public_api_exports_core_symbols() -> None:
    assert FilterSchema.__name__ == 'FilterSchema'
    assert RelationFilterSchema.__name__ == 'RelationFilterSchema'
    assert HavingFilterSchema.__name__ == 'HavingFilterSchema'
    assert OrderBySchema.__name__ == 'OrderBySchema'
    assert ResolvedOrderBySchema.__name__ == 'ResolvedOrderBySchema'
    assert PaginationSchema.__name__ == 'PaginationSchema'
    assert OperatorEnum.EQ.value == 'eq'
    assert OperationEnum.AND.value == '_and'
    assert OrderDirectionEnum.ASC.value == 'asc'
    assert callable(parse_filter_key)
    assert callable(parse_order_by_string)
    assert callable(format_like_value)


def test_layered_public_api_exports_integrations() -> None:
    assert CoreFilter.__name__ == 'CoreFilter'
    assert BaseQueryAdapter.__name__ == 'BaseQueryAdapter'
    assert SQLAlchemyQueryAdapter.__name__ == 'SQLAlchemyQueryAdapter'
