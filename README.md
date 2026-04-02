# qry

`qry` es una libreria para definir filtros, ordenamiento y paginacion de forma reusable, sin dejar que FastAPI o SQLAlchemy dominen todo el diseno.

## Objetivos

- `core` sin dependencias externas.
- Compatibilidad con Python `3.10+`.
- Integracion HTTP opcional para FastAPI.
- Integracion ORM opcional para SQLAlchemy `2.x`.
- Compatibilidad del core con Pydantic `v1` y `v2`; la integracion FastAPI sigue la matriz compatible de FastAPI.

## Mejoras frente a `base_filter.py`

El archivo original mezcla:

- contrato HTTP (`FastAPI`, `Query`, `Pydantic`)
- parsing de filtros y ordenamiento
- ejecucion ORM con SQLAlchemy
- gestion de joins y eager loading

Eso funciona para un proyecto puntual, pero como libreria complica:

- versionado de dependencias
- testing aislado
- extensibilidad hacia otros ORMs
- mantenimiento del API publico

Por eso esta base separa la libreria en capas:

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

## Instalacion

Core solamente:

```bash
pip install .
```

FastAPI + Pydantic:

```bash
pip install .[fastapi]
```

SQLAlchemy 2.x:

```bash
pip install .[sqlalchemy]
```

Todo:

```bash
pip install .[fastapi,sqlalchemy]
```

## API base

### Core

- `OperatorEnum`
- `OperationEnum`
- `OrderDirectionEnum`
- `FilterSchema`
- `RelationFilterSchema`
- `HavingFilterSchema`
- `OrderBySchema`
- `ResolvedOrderBySchema`
- `PaginationSchema`
- `parse_order_by_string()`
- `parse_filter_key()`
- `format_like_value()`

### FastAPI

`CoreFilter` vive en `qry.http` y:

- valida `order_by`, `page_number` y `page_size`
- transforma campos del modelo en `FilterSchema`
- resuelve relation filters y having filters
- mantiene una capa de compatibilidad para Pydantic, pero la integracion FastAPI depende de versiones compatibles entre FastAPI y Pydantic

### SQLAlchemy

`SQLAlchemyQueryAdapter` recibe estructuras del core y construye el `Select` o `Update`.

Rutas publicas recomendadas:

```python
from qry.http import CoreFilter
from qry.orm.base import BaseQueryAdapter
from qry.orm.sqlalchemy import SQLAlchemyQueryAdapter
```

Soporta:

- filtros directos
- filtros sobre relaciones
- `having`
- `order by`
- paginacion
- joins declarativos
- eager loading simple y sub-relations

## Diseno y trade-offs

### Lo que se mantiene

- la idea de `CoreFilter` como contrato reutilizable para endpoints
- la ergonomia del parsing `field__operator`
- la flexibilidad de joins declarativos

### Lo que cambia

- el `core` ya no depende de Pydantic
- SQLAlchemy queda encapsulado en un adapter
- la compatibilidad Pydantic del core esta aislada, pero FastAPI no soporta cualquier combinacion con Pydantic v1/v2
- se usa `src/` layout para empaquetado real

### Lo que deliberadamente no hice aun

- parser de filtros booleanos compuestos (`_and`, `_or`) a nivel HTTP
- adapters para Django ORM o Tortoise
- serializacion OpenAPI avanzada para filtros dinamicos

## Ejemplo rapido

```python
from sqlalchemy import select

from qry.http import CoreFilter
from qry.orm.sqlalchemy import SQLAlchemyQueryAdapter


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


filter_input = UserFilter(email__ilike="gmail.com", order_by="-created_at")
adapter = SQLAlchemyQueryAdapter()

stmt = adapter.build(
    query=select(User),
    model=User,
    filters=filter_input.model_filters,
    relation_filters=filter_input.relation_filtering_fields,
    order_by=filter_input.ordering_fields,
    pagination=filter_input.pagination,
)
```

## API publica estable

Los imports publicos recomendados y estables para consumidores son:

```python
from qry import FilterSchema, PaginationSchema, parse_filter_key
from qry.http import CoreFilter
from qry.orm.base import BaseQueryAdapter
from qry.orm.sqlalchemy import SQLAlchemyQueryAdapter
```

Rutas internas como `qry.http.fastapi` y `qry.orm.sqlalchemy_adapter.*` deben tratarse como detalles de implementacion.

## Matriz de compatibilidad actual

- Python: `3.10`, `3.11`, `3.12`, `3.13`
- Core: sin dependencias obligatorias de framework
- HTTP: `fastapi>=0.110,<1` con `pydantic>=2,<3`
- ORM: `sqlalchemy>=2,<3`

## Estado actual de validacion

- Hay tests unitarios para parsing y schemas base.
- Se agrego una suite inicial para API publica, `CoreFilter` y adapter SQLAlchemy 2.0.
- La ejecucion real mostro que `fastapi>=0.110` requiere Pydantic v2. La compatibilidad v1/v2 debe tratarse por matriz de entornos y no como una sola combinacion de extras.

### Checklist antes de PyPI

- correr CI para `core` con `pydantic==1.x`
- correr CI para integracion HTTP con una matriz FastAPI/Pydantic compatible
- correr tests con extras `.[dev,fastapi,sqlalchemy]`
- fijar politica de versionado para imports publicos (`qry`, `qry.http`, `qry.orm.sqlalchemy`)

## Siguientes pasos recomendados

- agregar CI con una matriz para `pydantic==1.x` y `pydantic==2.x`
- sumar tests de SQLAlchemy 2.0 con modelos de prueba
- versionar el API publico de `qry`, `qry.http` y `qry.orm.sqlalchemy`

