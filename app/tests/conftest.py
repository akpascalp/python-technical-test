import os
import asyncio
from typing import AsyncGenerator, Generator, Any

import pytest
import pytest_asyncio
from faker import Faker
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from infrastructure.models.site import Site
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

def generate_site_data(index: int) -> dict:
    """Generate fake data for a site."""
    installation_date = fake.date_between(start_date="-5y", end_date="today")

    max_power = fake.pyfloat(min_value=10, max_value=50, right_digits=2)
    min_power = max_power * fake.pyfloat(min_value=0.1, max_value=0.3, right_digits=2)
    
    return {
        "name": f"Site {index}",
        "installation_date": installation_date,
        "max_power_megawatt": max_power,
        "min_power_megawatt": min_power,
        "userful_energy_at_1_megawatt": fake.pyfloat(min_value=0.6, max_value=0.95, right_digits=2),
    }

@pytest_asyncio.fixture
async def sample_sites(db: AsyncSession) -> list[Site]:
    """Create sample sites for testing with Faker."""
    sites = [Site(**generate_site_data(index=index)) for index in range(5)]
    db.add_all(sites)
    await db.commit()
    
    for site in sites:
        await db.refresh(site)
    
    return sites
