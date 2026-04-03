# qry

`qry` is a Python library for declarative filtering, ordering, and pagination.
It is designed to keep the query definition layer separate from the HTTP layer and the ORM layer, so the same filter concepts can be reused in different parts of an application.

The project is especially useful when you want to:
- define reusable filter contracts for list endpoints
- parse request inputs into structured filter objects
- translate those filters into SQLAlchemy 2.x queries
- keep your core filtering model independent from FastAPI and ORM implementation details

## Table of Contents

- [Why qry](#why-qry)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [How qry Works](#how-qry-works)
- [Public API](#public-api)
- [Core Concepts](#core-concepts)
- [FastAPI Integration](#fastapi-integration)
- [SQLAlchemy Integration](#sqlalchemy-integration)
- [Advanced Configuration](#advanced-configuration)
- [Compatibility Matrix](#compatibility-matrix)
- [Testing and Validation](#testing-and-validation)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)

## Why qry

Many projects start with filtering logic inside one large file or directly inside endpoint handlers.
That usually mixes together:
- HTTP validation
- parsing of operators such as `field__ilike`
- pagination and ordering rules
- ORM-specific query building
- relationship joins

That approach is fast at the beginning, but it becomes hard to test, version, and evolve.

`qry` separates those responsibilities into layers:
- `qry` for core reusable schemas and parsing helpers
- `qry.http` for HTTP-oriented filter contracts
- `qry.orm.sqlalchemy` for query execution on SQLAlchemy 2.x

## Architecture

```text
qry/
├── src/qry/
│   ├── compat/
│   │   └── pydantic.py
│   ├── core/
│   │   ├── enums.py
│   │   ├── parsing.py
│   │   └── schemas.py
│   ├── http/
│   │   └── fastapi.py
│   └── orm/
│       ├── base/
│       │   └── adapter.py
│       └── sqlalchemy_adapter/
│           ├── adapter.py
│           ├── join_manager.py
│           └── operators.py
├── examples/
├── tests/
└── pyproject.toml
```

### Layer responsibilities

#### `qry`
Pure reusable building blocks:
- enums for operators and ordering
- dataclass schemas for filters and pagination
- parsing helpers for `field__operator` and `order_by`

#### `qry.http`
Defines `CoreFilter`, a reusable input contract for list endpoints.
It turns validated request data into structured `qry` schemas.

#### `qry.orm.sqlalchemy`
Provides `SQLAlchemyQueryAdapter`, which consumes the structured schemas and applies them to SQLAlchemy statements.

## Installation

Install only what you need.

### Core only

```bash
pip install qry
```

### FastAPI integration

```bash
pip install 'qry[fastapi]'
```

### SQLAlchemy integration

```bash
pip install 'qry[sqlalchemy]'
```

### Full local development setup

```bash
pip install -e '.[dev,fastapi,sqlalchemy]'
```

## Quick Start

This is the smallest complete example showing the intended flow.

```python
from sqlalchemy import select

from qry.http import CoreFilter
from qry.orm.sqlalchemy import SQLAlchemyQueryAdapter


class UserFilter(CoreFilter):
    email__ilike: str | None = None
    status: str | None = None

    class FilterConfig:
        allowed_ordering_fields = ["email", "created_at"]


filters = UserFilter(
    email__ilike="gmail.com",
    status="active",
    order_by="-created_at",
    page_number=1,
    page_size=20,
)

adapter = SQLAlchemyQueryAdapter()
statement = adapter.build(
    query=select(User),
    model=User,
    filters=filters.model_filters,
    order_by=filters.ordering_fields,
    pagination=filters.pagination,
)
```

## How qry Works

The normal flow is:

1. Define a filter class that inherits from `CoreFilter`.
2. Receive filter data from code or HTTP query parameters.
3. Convert that input into structured schemas such as `FilterSchema` and `PaginationSchema`.
4. Pass those schemas to the ORM adapter.
5. Execute the resulting SQLAlchemy statement.

Conceptually:

```text
Request / Input
    -> CoreFilter
    -> FilterSchema / RelationFilterSchema / ResolvedOrderBySchema / PaginationSchema
    -> SQLAlchemyQueryAdapter
    -> SQLAlchemy Select / Update
```

## Public API

These are the recommended stable imports for consumers:

```python
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
```

Internal paths such as `qry.http.fastapi` and `qry.orm.sqlalchemy_adapter.*` should be treated as implementation details.

## Core Concepts

### Operators

Supported operators are defined in `OperatorEnum`:
- `eq`
- `neq`
- `gt`
- `gte`
- `lt`
- `lte`
- `in`
- `not_in`
- `is_null`
- `like`
- `ilike`
- `not`
- `between`
- `regex`

### Operator registry

`qry` describes every operator as a handler that builds the SQLAlchemy boolean expression. You can override any handler or register new behavior through `register_operator_handler` (or `register_operator`, a decorator that wraps it).

```python
from qry.core.enums import OperatorEnum
from qry.core.operator_registry import register_operator_handler


@register_operator_handler(OperatorEnum.LIKE)
def custom_like(column, value):
    return column.like(f\"%{value}%\") & column != \"blocked\"
```

The adapter always consults the registry when translating filters, so your custom handler runs everywhere `build_expression` is used (`CoreFilter` → `SQLAlchemyQueryAdapter`). Use `list_registered_operators()` when you need to inspect which handlers are available.

### Filter keys

`qry` uses the `field__operator` convention.

Examples:
- `email` -> equality
- `email__ilike` -> case-insensitive LIKE
- `age__gte` -> greater than or equal
- `status__in` -> IN list

### Ordering

`order_by` uses a comma-separated string:

```text
-created_at,+email
```

Rules:
- `-field` means descending
- `+field` means ascending
- `field` without prefix is treated as ascending

### Pagination

Pagination is represented by `PaginationSchema`:
- `page_number`
- `page_size`

A `page_size` of `0` disables the limit behavior in the adapter.

## FastAPI Integration

`CoreFilter` is designed to be subclassed in your application.

### Basic example

```python
from fastapi import Depends, FastAPI

from qry.http import CoreFilter


class UserFilter(CoreFilter):
    email__ilike: str | None = None
    status: str | None = None

    class FilterConfig:
        allowed_ordering_fields = ["email", "created_at"]


app = FastAPI()


@app.get("/users")
def list_users(filters: UserFilter = Depends()):
    return {
        "filters": [
            {"column": item.column, "operator": item.operator.value, "value": item.value}
            for item in filters.model_filters
        ]
    }
```

### What `CoreFilter` gives you

A `CoreFilter` instance exposes:
- `filtering_fields`: raw dict of non-reserved fields
- `model_filters`: list of `FilterSchema`
- `relation_filtering_fields`: list of `RelationFilterSchema`
- `having_filtering_fields`: list of `HavingFilterSchema`
- `ordering_fields`: list of `ResolvedOrderBySchema`
- `pagination`: `PaginationSchema`

### Reserved fields

These fields are handled internally and not treated as model filters:
- `order_by`
- `page_number`
- `page_size`

### `FilterConfig`

Each filter class can define a nested `FilterConfig` to control behavior.

Available options:
- `allowed_ordering_fields`
- `reject_invalid_ordering_fields` *(bool, defaults to `False`)* – if `True` (and there is an allowlist), `order_by` entries that fall outside the allowlist now raise `ValueError`.
- `relation_filters`
- `relation_order_by`
- `having_filters`

Example strict ordering configuration:

```python
class UserFilter(CoreFilter):
    class FilterConfig:
        allowed_ordering_fields = ["email", "created_at"]
        reject_invalid_ordering_fields = True
```

With this setup, `order_by='-created_at,+foo'` raises immediately because `foo` is not allowed, while `order_by='-email'` continues to work as before.

## SQLAlchemy Integration

`SQLAlchemyQueryAdapter` applies structured filter definitions to SQLAlchemy 2.x statements.

### Basic adapter usage

```python
from sqlalchemy import select

from qry.orm.sqlalchemy import SQLAlchemyQueryAdapter

adapter = SQLAlchemyQueryAdapter()
statement = adapter.build(
    query=select(User),
    model=User,
    filters=filters.model_filters,
    relation_filters=filters.relation_filtering_fields,
    order_by=filters.ordering_fields,
    having_filters=filters.having_filtering_fields,
    pagination=filters.pagination,
)
```

### Supported behaviors

The adapter supports:
- direct filters on the root model
- relation filters
- `having` expressions
- ordering (invalid columns or unsupported directions now raise a `ValueError` so that callers notice mistakes instead of generating invalid SQL)
- pagination
- eager loading for relations
- sub-relation loading

### Pagination behavior

If `pagination.page_size > 0`, the adapter applies:
- `LIMIT page_size`
- `OFFSET (page_number - 1) * page_size`

If `page_size == 0`, pagination is skipped.

### Counting pages

```python
pages = adapter.calculate_num_pages(total_results=125, pagination=filters.pagination)
```

## Advanced Configuration

### Relation filters

You can map request fields to a related model or to a legacy join path.

```python
class UserFilter(CoreFilter):
    company_id: int | None = None

    class FilterConfig:
        relation_filters = {
            "company_id": Company,
        }
```

This allows `company_id` to become a `RelationFilterSchema` that the SQLAlchemy adapter resolves through joins.

### Relation ordering

You can expose an ordering alias that maps to a different underlying field.

```python
class UserFilter(CoreFilter):
    class FilterConfig:
        allowed_ordering_fields = ["company_name"]
        relation_order_by = {
            "company_name": ("name", Company),
        }
```

Now `order_by=+company_name` is resolved to `Company.name ASC`.

### Having filters

You can bind a filter field to an aggregate SQL function.

```python
class ReportFilter(CoreFilter):
    total__gte: int | None = None

    class FilterConfig:
        having_filters = {
            "total__gte": func.count(User.id),
        }
```

### List inputs

If a field value is a Python list and no explicit operator is provided, `CoreFilter` promotes it to `OperatorEnum.IN`.

## Full Example

```python
from fastapi import Depends, FastAPI
from sqlalchemy import ForeignKey, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from qry.http import CoreFilter
from qry.orm.sqlalchemy import SQLAlchemyQueryAdapter


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[str] = mapped_column(String(64))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    company: Mapped[Company] = relationship()


class UserFilter(CoreFilter):
    email__ilike: str | None = None
    company_id: int | None = None

    class FilterConfig:
        allowed_ordering_fields = ["id", "email", "created_at", "company_name"]
        relation_filters = {
            "company_id": Company,
        }
        relation_order_by = {
            "company_name": ("name", Company),
        }


app = FastAPI()
adapter = SQLAlchemyQueryAdapter()


@app.get("/users")
def list_users(filters: UserFilter = Depends()):
    statement = adapter.build(
        query=select(User),
        model=User,
        filters=filters.model_filters,
        relation_filters=filters.relation_filtering_fields,
        order_by=filters.ordering_fields,
        pagination=filters.pagination,
    )
    return {"sql": str(statement)}
```

## Compatibility Matrix

Current supported matrix:
- Python: `3.10`, `3.11`, `3.12`, `3.13`
- Core: framework-independent
- HTTP integration: `fastapi>=0.110,<1` with `pydantic>=2,<3`
- SQLAlchemy integration: `sqlalchemy>=2,<3`

### Important note about Pydantic

The core compatibility helpers are designed to bridge Pydantic differences, but the FastAPI integration depends on FastAPI's own supported version matrix.
That means you should not treat `qry` as universally compatible with every FastAPI and Pydantic v1/v2 combination.

## Testing and Validation

Current validation status:
- parsing and schema tests
- public API contract tests
- `CoreFilter` behavior tests
- SQLAlchemy adapter tests
- edge case tests
- package build smoke test

Local validation commands:

```bash
python3 -m pytest
python3 -m ruff check .
python3 -m build
```

## Development

### Editable install

```bash
python3 -m pip install -e '.[dev,fastapi,sqlalchemy]'
```

### Project checks

```bash
python3 -m pytest
python3 -m ruff check .
python3 -m build
```

### CI

A GitHub Actions workflow is included to validate:
- Python 3.10 to 3.13
- tests
- Ruff

## Troubleshooting

### My filter is ignored

Possible reasons:
- the field is `None`
- the field is reserved (`order_by`, `page_number`, `page_size`)
- the ordering field is not present in `allowed_ordering_fields`

### Relation ordering does not work

Check:
- the field is in `allowed_ordering_fields`
- the field is mapped in `relation_order_by`
- the mapped target is a valid SQLAlchemy model or relationship target

### FastAPI import errors with Pydantic v1

This usually means the installed FastAPI version expects Pydantic v2.
Use a compatible FastAPI/Pydantic combination based on the version matrix you support.

### Build warnings about metadata

If build warnings appear, check `pyproject.toml` first.
Packaging metadata is one of the most common sources of avoidable release issues.

## Roadmap

Near-term priorities:
- expand CI to validate more compatibility combinations by layer
- add more edge case tests around joins and invalid configuration
- document release/versioning policy for public imports
- consider future adapters beyond SQLAlchemy

## License

MIT
