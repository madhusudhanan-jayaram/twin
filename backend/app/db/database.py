from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.schemas import Warehouse

engine = create_async_engine(settings.database_url, echo=False)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def get_engine():
    return engine


async def get_session():
    async with async_session() as session:
        yield session


SEED_WAREHOUSES = [
    Warehouse(
        name="OKC Pharma Cold Storage",
        city="Oklahoma City",
        state="OK",
        lat=35.4676,
        lng=-97.5164,
        available_capacity=500,
        temp_min=2.0,
        temp_max=8.0,
    ),
    Warehouse(
        name="Tulsa BioLogistics Hub",
        city="Tulsa",
        state="OK",
        lat=36.1540,
        lng=-95.9928,
        available_capacity=300,
        temp_min=2.0,
        temp_max=8.0,
    ),
    Warehouse(
        name="Wichita Cold Vault",
        city="Wichita",
        state="KS",
        lat=37.6872,
        lng=-97.3301,
        available_capacity=400,
        temp_min=2.0,
        temp_max=8.0,
    ),
    Warehouse(
        name="Springfield MedStore",
        city="Springfield",
        state="MO",
        lat=37.2090,
        lng=-93.2923,
        available_capacity=250,
        temp_min=2.0,
        temp_max=8.0,
    ),
    Warehouse(
        name="St. Louis Pharma Depot",
        city="St. Louis",
        state="MO",
        lat=38.6270,
        lng=-90.1994,
        available_capacity=600,
        temp_min=2.0,
        temp_max=8.0,
    ),
]


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session() as session:
        from sqlmodel import select
        result = await session.execute(select(Warehouse))
        if not result.scalars().first():
            for wh in SEED_WAREHOUSES:
                session.add(wh)
            await session.commit()
