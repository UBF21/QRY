import pytest

from qry.core.enums import OperatorEnum, OrderDirectionEnum
from qry.http import CoreFilter


class DemoFilter(CoreFilter):
    email__ilike: str | None = None
    status: str | None = None
    company_id: int | None = None
    total__gte: int | None = None

    class FilterConfig:
        allowed_ordering_fields = ['email', 'created_at', 'company_name']
        relation_filters = {
            'company_id': 'Company',
        }
        relation_order_by = {
            'company_name': ('name', 'Company'),
        }
        having_filters = {
            'total__gte': 'TOTAL_FUNC',
        }


def test_core_filter_builds_structured_filters() -> None:
    filters = DemoFilter(
        email__ilike='gmail.com',
        status='active',
        company_id=7,
        total__gte=10,
        order_by='-created_at,+company_name',
        page_number=2,
        page_size=25,
    )

    assert filters.filtering_fields == {
        'email__ilike': 'gmail.com',
        'status': 'active',
    }

    assert [(item.column, item.operator, item.value) for item in filters.model_filters] == [
        ('email', OperatorEnum.ILIKE, 'gmail.com'),
        ('status', OperatorEnum.EQ, 'active'),
    ]

    assert [(item.column, item.operator, item.value, item.target) for item in filters.relation_filtering_fields] == [
        ('company_id', OperatorEnum.EQ, 7, 'Company'),
    ]

    assert [(item.column, item.operator, item.value, item.func) for item in filters.having_filtering_fields] == [
        ('total', OperatorEnum.GTE, 10, 'TOTAL_FUNC'),
    ]

    assert [(item.column, item.direction, item.target) for item in filters.ordering_fields] == [
        ('created_at', OrderDirectionEnum.DESC, None),
        ('name', OrderDirectionEnum.ASC, 'Company'),
    ]

    assert filters.pagination.page_number == 2
    assert filters.pagination.page_size == 25


def test_core_filter_promotes_list_values_to_in_operator() -> None:
    class ListFilter(CoreFilter):
        status: list[str] | None = None

    filters = ListFilter(status=['active', 'pending'])

    assert len(filters.model_filters) == 1
    assert filters.model_filters[0].column == 'status'
    assert filters.model_filters[0].operator == OperatorEnum.IN
    assert filters.model_filters[0].value == ['active', 'pending']


def test_core_filter_rejects_disallowed_ordering_fields() -> None:
    class StrictFilter(CoreFilter):
        order_by: str | None = None

        class FilterConfig:
            allowed_ordering_fields = ['name']
            reject_invalid_ordering_fields = True

    filters = StrictFilter(order_by='-created_at')

    with pytest.raises(ValueError) as excinfo:
        _ = filters.ordering_fields

    assert "Ordering field 'created_at' is not allowed." in str(excinfo.value)


def test_core_filter_can_ignore_ordering_errors() -> None:
    class LenientFilter(CoreFilter):
        order_by: str | None = None

        class FilterConfig:
            allowed_ordering_fields = ['name']
            reject_invalid_ordering_fields = False

    filters = LenientFilter(order_by='-created_at')

    assert filters.ordering_fields == []
