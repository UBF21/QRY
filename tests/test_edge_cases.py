import pytest
from sqlalchemy import column

from qry.core.enums import OperatorEnum, OrderDirectionEnum
from qry.core.parsing import format_like_value, parse_filter_key, parse_order_by_string
from qry.core.schemas import PaginationSchema
from qry.http import CoreFilter
from qry.orm.sqlalchemy_adapter.operators import build_expression


class EdgeFilter(CoreFilter):
    status: str | None = None

    class FilterConfig:
        allowed_ordering_fields = ['created_at']


def test_parse_filter_key_raises_for_unknown_operator() -> None:
    with pytest.raises(ValueError):
        parse_filter_key('email__contains')


def test_parse_order_by_string_ignores_empty_and_disallowed_entries() -> None:
    parsed = parse_order_by_string(' , -created_at, +ignored, ', allowed_fields={'created_at'})

    assert [(item.column, item.direction) for item in parsed] == [
        ('created_at', OrderDirectionEnum.DESC),
    ]


def test_format_like_value_preserves_existing_wildcards() -> None:
    assert format_like_value('%foo%') == '%foo%'


def test_core_filter_ignores_disallowed_ordering_fields() -> None:
    filters = EdgeFilter(order_by='-created_at,+email')

    assert [(item.column, item.direction) for item in filters.ordering_fields] == [
        ('created_at', OrderDirectionEnum.DESC),
    ]


def test_build_expression_supports_between_operator() -> None:
    expression = build_expression(column('age'), OperatorEnum.BETWEEN, (18, 30))

    compiled = str(expression.compile(compile_kwargs={'literal_binds': True}))
    assert 'BETWEEN 18 AND 30' in compiled


def test_pagination_schema_allows_disabling_limit_with_zero_page_size() -> None:
    pagination = PaginationSchema(page_number=1, page_size=0)

    assert pagination.page_size == 0
