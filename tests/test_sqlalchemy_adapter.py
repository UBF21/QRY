import pytest

from sqlalchemy import ForeignKey, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from qry.core.enums import OperatorEnum, OrderDirectionEnum
from qry.core.schemas import FilterSchema, HavingFilterSchema, PaginationSchema, RelationFilterSchema, ResolvedOrderBySchema
from qry.orm.sqlalchemy import SQLAlchemyQueryAdapter


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = 'companies'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id'))
    company: Mapped[Company] = relationship()


def setup_database() -> Session:
    engine = create_engine('sqlite+pysqlite:///:memory:')
    Base.metadata.create_all(engine)
    session = Session(engine)

    acme = Company(id=1, name='Acme')
    beta = Company(id=2, name='Beta')
    session.add_all([
        acme,
        beta,
        User(id=1, email='ana@acme.com', status='active', company=acme),
        User(id=2, email='bruno@beta.com', status='inactive', company=beta),
        User(id=3, email='carla@acme.com', status='active', company=acme),
    ])
    session.commit()
    return session


def test_sqlalchemy_adapter_applies_filters_ordering_and_pagination() -> None:
    session = setup_database()
    adapter = SQLAlchemyQueryAdapter()

    statement = adapter.build(
        query=select(User),
        model=User,
        filters=[FilterSchema(column='status', operator=OperatorEnum.EQ, value='active')],
        relation_filters=[RelationFilterSchema(column='name', operator=OperatorEnum.EQ, value='Acme', target=Company)],
        order_by=[ResolvedOrderBySchema(column='email', direction=OrderDirectionEnum.ASC)],
        pagination=PaginationSchema(page_number=1, page_size=10),
    )

    rows = session.execute(statement).scalars().all()

    assert [user.email for user in rows] == ['ana@acme.com', 'carla@acme.com']


def test_sqlalchemy_adapter_applies_having_filters() -> None:
    session = setup_database()
    adapter = SQLAlchemyQueryAdapter()

    statement = adapter.build(
        query=select(User.company_id, func.count(User.id).label('total')).group_by(User.company_id),
        model=User,
        having_filters=[
            HavingFilterSchema(
                column='total',
                func=func.count(User.id),
                value=2,
                operator=OperatorEnum.GTE,
            )
        ],
        order_by=[ResolvedOrderBySchema(column='company_id', direction=OrderDirectionEnum.ASC)],
    )

    rows = session.execute(statement).all()

    assert rows == [(1, 2)]


def test_sqlalchemy_adapter_rejects_unknown_order_column() -> None:
    session = setup_database()
    adapter = SQLAlchemyQueryAdapter()

    with pytest.raises(ValueError) as excinfo:
        adapter.build(
            query=select(User),
            model=User,
            order_by=[ResolvedOrderBySchema(column='unknown', direction=OrderDirectionEnum.ASC)],
        )

    assert "Ordering column 'unknown' not found on model 'User'." in str(excinfo.value)
