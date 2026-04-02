from qry.core.schemas import PaginationSchema


def test_pagination_schema_defaults() -> None:
    pagination = PaginationSchema()

    assert pagination.page_number == 1
    assert pagination.page_size == 10
