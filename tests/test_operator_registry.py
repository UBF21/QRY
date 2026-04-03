from sqlalchemy.sql import column

from qry.core.enums import OperatorEnum
from qry.core.operator_registry import get_operator_handler, list_registered_operators, register_operator_handler
from qry.orm.sqlalchemy_adapter.operators import build_expression


def test_register_operator_handler_overrides_behavior() -> None:
    column_ref = column('name')
    original_handler = get_operator_handler(OperatorEnum.EQ)

    def custom_eq(column_value, value):
        return ('custom', column_value.name, value)

    register_operator_handler(OperatorEnum.EQ, custom_eq)

    try:
        result = build_expression(column_ref, OperatorEnum.EQ, 'foo')
        assert result == ('custom', 'name', 'foo')
    finally:
        register_operator_handler(OperatorEnum.EQ, original_handler)


def test_regex_operator_produces_expected_sql() -> None:
    expr = build_expression(column('email'), OperatorEnum.REGEX, '^a')
    assert 'REGEXP' in str(expr).upper()

def test_list_registered_operators_contains_core_values() -> None:
    registered = list_registered_operators()
    assert OperatorEnum.EQ in registered
    assert OperatorEnum.LIKE in registered
