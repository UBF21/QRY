from __future__ import annotations

from fastapi import FastAPI, Depends
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
def list_users(filters: UserFilter = Depends()) -> dict[str, str]:
    statement = adapter.build(
        query=select(User),
        model=User,
        filters=filters.model_filters,
        relation_filters=filters.relation_filtering_fields,
        order_by=filters.ordering_fields,
        pagination=filters.pagination,
    )

    return {"sql": str(statement)}

