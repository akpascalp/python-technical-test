from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import with_polymorphic, selectinload

from infrastructure.validators import (
    validate_french_site_date,
    validate_italian_site_date,
    validate_site_group_association
)
from infrastructure.models.site import SiteCountry, Site, SiteFrance, SiteItaly
from infrastructure.models.group import Group
from infrastructure.schemas.site import SiteFranceCreate, SiteItalyCreate, SiteBase, SiteRead
from infrastructure.crud.crud_sites import site_crud, site_france_crud, site_italy_crud


async def create_french_site(db: AsyncSession, site: SiteFranceCreate):
    if site.installation_date:
        valid = await validate_french_site_date(db, site.installation_date)
        if not valid:
            raise HTTPException(
                status_code=422, detail="Only one French site can be installed per day"
            )

    return await site_france_crud.create(db=db, object=site)


async def create_italian_site(db: AsyncSession, site: SiteItalyCreate):
    if site.installation_date:
        valid = await validate_italian_site_date(site.installation_date)
        if not valid:
            raise HTTPException(
                status_code=422, detail="Italian sites must be installed on weekends"
            )

    return await site_italy_crud.create(db=db, object=site)


async def update_site(db: AsyncSession, site_id: int, site_update: SiteBase):
    site = await site_crud.get(db=db, id=site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    if hasattr(site_update, "installation_date") and site_update.installation_date:
        if site["country"] == SiteCountry.france:
            valid = await validate_french_site_date(
                db, site_update.installation_date, exclude_site_id=site_id
            )
            if not valid:
                raise HTTPException(
                    status_code=422, detail="Only one French site can be installed per day"
                )
        elif site["country"] == SiteCountry.italy:
            valid = await validate_italian_site_date(site_update.installation_date)
            if not valid:
                raise HTTPException(
                    status_code=422, detail="Italian sites must be installed on weekends"
                )

    updated_site = await site_crud.update(
        db=db, object=site_update, id=site_id, return_as_model=True, schema_to_select=SiteRead
    )
    return updated_site


async def add_site_to_group(db: AsyncSession, site_id: int, group_id: int):
    valid = await validate_site_group_association(db, site_id, group_id)
    if not valid:
        raise HTTPException(
            status_code=422, detail="Invalid association between site and group"
        )
    
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    PolymorphicSite = with_polymorphic(Site, [SiteFrance, SiteItaly])
    
    result = await db.execute(
        select(PolymorphicSite)
        .options(selectinload(PolymorphicSite.groups))
        .where(PolymorphicSite.id == site_id)
    )
    
    site_model = result.unique().scalar_one_or_none()
    if not site_model:
        raise HTTPException(status_code=404, detail="Site not found")

    if group not in site_model.groups:
        site_model.groups.append(group)
        
        await db.commit()

    return None
