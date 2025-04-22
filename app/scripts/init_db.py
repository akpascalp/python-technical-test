import asyncio
import random
from datetime import date, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from infrastructure.db import async_session_maker, Base
from infrastructure.models.site import Site, SiteFrance, SiteItaly, SiteCountry
from infrastructure.models.group import Group, GroupType


async def is_database_seeded(session: AsyncSession):
    """Check if the database is already seeded."""
    result = await session.execute(select(Site))
    return result.first() is not None


async def generate_seed_data(session: AsyncSession):
    """Generate and insert sample data into the database."""
    french_sites = []
    for i in range(1, 6):
        install_date = date.today() - timedelta(days=i*3)
        french_site = SiteFrance(
            name=f"Site France {i}",
            installation_date=install_date,
            max_power_megawatt=random.uniform(10.0, 50.0),
            min_power_megawatt=random.uniform(1.0, 5.0),
            useful_energy_at_1_megawatt=random.uniform(0.7, 0.95),
            country=SiteCountry.FRANCE
        )
        french_sites.append(french_site)

    italian_sites = []
    for i in range(1, 6):
        days_until_weekend = (5 - date.today().weekday() + (i-1)*7) % 7
        if days_until_weekend == 0:
            install_date = date.today() + timedelta(days=(i-1)*7)
        else:
            install_date = date.today() + timedelta(days=days_until_weekend + (i-1)*7)
        
        italian_site = SiteItaly(
            name=f"Site Italia {i}",
            installation_date=install_date,
            max_power_megawatt=random.uniform(15.0, 60.0),
            min_power_megawatt=random.uniform(2.0, 8.0),
            efficiency=random.uniform(0.6, 0.9),
            country=SiteCountry.ITALY
        )
        italian_sites.append(italian_site)

    all_sites = french_sites + italian_sites
    session.add_all(all_sites)
    await session.commit()

    for site in all_sites:
        await session.refresh(site)

    groups = [
        Group(name=f"Groupe {i}", type=[GroupType.GROUP1, GroupType.GROUP2, GroupType.GROUP3][i % 3])
        for i in range(1, 5)
    ]
    
    session.add_all(groups)
    await session.commit()

    valid_groups = [group for group in groups if group.type != GroupType.GROUP3]

    for site in all_sites:
        selected_group_count = min(len(valid_groups), random.randint(1, 2))
        selected_groups = random.sample(valid_groups, k=selected_group_count)
        
        for group in selected_groups:
            await session.execute(
                text("INSERT INTO site_group (site_id, group_id) VALUES (:site_id, :group_id)"),
                {"site_id": site.id, "group_id": group.id}
            )

    if len(groups) >= 3:
        groups[2].parent_id = groups[0].id
    
    await session.commit()

    print(f"Seeded {len(french_sites)} French sites, {len(italian_sites)} Italian sites, and {len(groups)} groups.")
    # print(f"Created {sum(len(site.groups) for site in all_sites)} site-group associations.")


async def seed_data():
    """Seed database with sample data."""
    async with async_session_maker() as session:
        if await is_database_seeded(session):
            print("Data already seeded. Purging and reseeding...")
            await session.execute(text("DELETE FROM site_group"))
            await session.execute(text("DELETE FROM sites"))
            await session.execute(text("DELETE FROM groups"))
            await session.commit()
            
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
