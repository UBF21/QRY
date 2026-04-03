import pytest

from qry.core.enums import OperatorEnum, OrderDirectionEnum
from qry.core.parsing import format_like_value, parse_filter_key, parse_order_by_string


def test_format_like_value_wraps_both_sides() -> None:
    assert format_like_value("foo") == "%foo%"


def test_parse_filter_key_defaults_to_eq() -> None:
    assert parse_filter_key("email") == ("email", OperatorEnum.EQ)


def test_parse_filter_key_extracts_operator() -> None:
    assert parse_filter_key("email__ilike") == ("email", OperatorEnum.ILIKE)


def test_parse_filter_key_rejects_unknown_operator() -> None:
    with pytest.raises(ValueError) as excinfo:
        parse_filter_key("name__unknown")

    assert "Invalid operator 'unknown' in filter 'name__unknown'." in str(excinfo.value)


def test_parse_order_by_string_respects_signs_and_allowlist() -> None:
    parsed = parse_order_by_string(
        "-created_at,+email,+ignored",
        allowed_fields={"created_at", "email"},
    )

    assert [item.column for item in parsed] == ["created_at", "email"]
    assert [item.direction for item in parsed] == [
        OrderDirectionEnum.DESC,
        OrderDirectionEnum.ASC,
    ]


def test_parse_order_by_string_rejects_disallowed_when_strict() -> None:
    with pytest.raises(ValueError) as excinfo:
        parse_order_by_string(
            "-name,+nickname",
            allowed_fields={"name"},
            raise_on_invalid=True,
        )

    assert "Ordering field 'nickname' is not allowed." in str(excinfo.value)
