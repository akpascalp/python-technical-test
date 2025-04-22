from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.models.site import SiteFrance

async def validate_french_site_date(
    db: AsyncSession, 
    installation_date: date,
    exclude_site_id: int = None
) -> bool:
    """
    Check if a french site with same date does not already exists (only 1 french site per day can be created).
    Return True if the date is valid, otherwise False.
    """
    query = select(SiteFrance).where(SiteFrance.installation_date == installation_date)
    
    if exclude_site_id is not None:
        query = query.where(SiteFrance.id != exclude_site_id)
    
    result = await db.execute(query)
    existing_site = result.scalars().first()
    
    return existing_site is None

async def validate_italian_site_date(installation_date: date) -> bool:
    """
    Check if the installation date of the italian site is a weekend.
    Return True if the date is valid, otherwise False.
    """
    weekday = installation_date.weekday()
    return weekday >= 5  # 5=saturday, 6=sunday
