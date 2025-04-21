import asyncio
import random
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from infrastructure.db import async_session_maker, Base
from infrastructure.models.site import Site
from infrastructure.models.group import Group, GroupType


async def is_database_seeded(session: AsyncSession):
    """Check if the database is already seeded."""
    result = await session.execute(select(Site))
    return result.first() is not None


async def generate_seed_data(session: AsyncSession):
    """Generate and insert sample data into the database."""
    sites = [
        Site(
            name=f"Site {i}",
            installation_date=date.today() - timedelta(days=random.randint(1, 1000)),
            max_power_megawatt=random.uniform(10.0, 50.0),
            min_power_megawatt=random.uniform(1.0, 5.0),
            useful_energy_at_1_megawatt=random.uniform(0.7, 0.95),
            groups=[],
        )
        for i in range(1, 11)
    ]

    session.add_all(sites)
    await session.commit()

    # Refresh sites to get their IDs
    for site in sites:
        await session.refresh(site)

    groups = [
        Group(name=f"Groupe {i}", type=[GroupType.GROUP1, GroupType.GROUP2, GroupType.GROUP3][i % 3])
        for i in range(1, 5)
    ]

    session.add_all(groups)
    await session.commit()

    print(f"Seeded {len(sites)} sites and {len(groups)} groups.")


async def seed_data():
    """Seed database with sample data."""
    async with async_session_maker() as session:
        if await is_database_seeded(session):
            print("Data already seeded.")
        else:
            print("Seeding database with test data...")
            await generate_seed_data(session)
            print("Seeding completed.")

async def main():
    engine = create_async_engine("postgresql+asyncpg://user:password@db/dbname")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await seed_data()

if __name__ == "__main__":
    asyncio.run(main())
