import os
import asyncio
from typing import Any
from collections.abc import AsyncGenerator, Generator
from datetime import date, timedelta

import pytest
import pytest_asyncio
from faker import Faker
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import with_polymorphic

from main import app
from infrastructure.models.site import Site, SiteFrance, SiteItaly, SiteCountry
from infrastructure.models.group import Group, GroupType
from infrastructure.db import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "postgres")

TEST_DB_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db/{POSTGRES_DB}"

async_engine = create_async_engine(TEST_DB_URL)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

fake = Faker()


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, Any, None]:
    with TestClient(app) as _client:
        yield _client
    app.dependency_overrides = {}


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(base_url="http://test") as client:
        from httpx import ASGITransport

        client.transport = ASGITransport(app=app)
        yield client


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


def generate_site_france_data(index: int) -> dict:
    """Generate fake data for a French site."""
    installation_date = date.today() - timedelta(
        days=index * 5
    )  # Use unique dates for French sites

    max_power = fake.pyfloat(min_value=10, max_value=50, right_digits=2)
    min_power = max_power * fake.pyfloat(min_value=0.1, max_value=0.3, right_digits=2)

    return {
        "name": f"Site France {index}",
        "installation_date": installation_date,
        "max_power_megawatt": max_power,
        "min_power_megawatt": min_power,
        "useful_energy_at_1_megawatt": fake.pyfloat(min_value=0.7, max_value=0.95, right_digits=2),
        "country": SiteCountry.france,
    }


def generate_site_italy_data(index: int) -> dict:
    """Generate fake data for an Italian site."""
    # Calculate a weekend date (5=Saturday, 6=Sunday)
    today = date.today()
    weekday = today.weekday()
    days_until_saturday = (5 - weekday) % 7  # 5 = Saturday
    weekend_date = today + timedelta(
        days=days_until_saturday + (index * 7)
    )  # Each site on a different weekend

    max_power = fake.pyfloat(min_value=15, max_value=60, right_digits=2)
    min_power = max_power * fake.pyfloat(min_value=0.1, max_value=0.3, right_digits=2)

    return {
        "name": f"Site Italy {index}",
        "installation_date": weekend_date,
        "max_power_megawatt": max_power,
        "min_power_megawatt": min_power,
        "efficiency": fake.pyfloat(min_value=0.6, max_value=0.9, right_digits=2),
        "country": SiteCountry.italy,
    }


def generate_group_data(index: int) -> dict:
    """Generate fake data for a group."""
    return {
        "name": f"Group {index}",
        "type": fake.random_element(
            elements=(GroupType.GROUP1, GroupType.GROUP2, GroupType.GROUP3)
        ),
    }


@pytest_asyncio.fixture
async def sample_sites(db: AsyncSession) -> list[Site]:
    """Create sample sites (both French and Italian) for testing."""
    # Create 3 French sites
    french_sites = [SiteFrance(**generate_site_france_data(index=index)) for index in range(3)]
    db.add_all(french_sites)
    # await db.commit()

    # Create 3 Italian sites
    italian_sites = [SiteItaly(**generate_site_italy_data(index=index)) for index in range(3)]
    db.add_all(italian_sites)
    await db.commit()

    polymorphicSite = with_polymorphic(Site, [SiteFrance, SiteItaly])
    result = await db.execute(select(polymorphicSite))
    sites = list(result.scalars().all())

    return sites


@pytest_asyncio.fixture
async def sample_french_sites(db: AsyncSession) -> list[SiteFrance]:
    """Create sample French sites for testing."""
    french_sites = [SiteFrance(**generate_site_france_data(index)) for index in range(3)]
    db.add_all(french_sites)
    await db.commit()

    for site in french_sites:
        await db.refresh(site)

    return french_sites


@pytest_asyncio.fixture
async def sample_italian_sites(db: AsyncSession) -> list[SiteItaly]:
    """Create sample Italian sites for testing."""
    italian_sites = [SiteItaly(**generate_site_italy_data(index)) for index in range(3)]
    db.add_all(italian_sites)


@pytest_asyncio.fixture
async def sample_groups(db: AsyncSession) -> list[Group]:
    """Create sample groups for testing."""
    groups = [Group(**generate_group_data(index)) for index in range(3)]
    db.add_all(groups)
    await db.commit()

    for group in groups:
        await db.refresh(group)

    return groups
