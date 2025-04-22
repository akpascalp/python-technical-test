from datetime import date
from typing import Any
from enum import Enum

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from fastcrud.paginated import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from infrastructure.models.site import Site as SiteModel
from infrastructure.models.site import SiteFrance, SiteItaly
from infrastructure.models.site import SiteCountry
from infrastructure.models.group import Group

from infrastructure.db import get_session
from infrastructure.schemas.site import SiteRead, Site, SiteBase, SiteWithGroups, SiteFranceCreate, SiteItalyCreate
from infrastructure.crud.crud_sites import site_crud, site_france_crud, site_italy_crud

router = APIRouter()

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


@router.get("/", response_model=PaginatedListResponse[SiteWithGroups])
async def read_sites(
    db: AsyncSession = Depends(get_session),
    page: int = 1,
    items_per_page: int = 10,
    limit: int = 100,
    name: str | None = None,
    max_power_megawatt: float | None = None,
    min_power_megawatt: float | None = None,
    installation_date_from: date | None = None,
    installation_date_to: date | None = None,
    useful_energy_at_1_megawatt: float | None = None,
    efficiency: float | None = None,
    sort_by: str | None = Query(None, description="Field to sort by"),
    sort_order: SortOrder = SortOrder.desc,
) -> dict:
    """
    Get all sites with filtering and sorting options.
    """
    filters = {}

    if name is not None:
        filters["name"] = name
        
    if max_power_megawatt is not None:
        filters["max_power_megawatt"] = max_power_megawatt

    if min_power_megawatt is not None:
        filters["min_power_megawatt"] = min_power_megawatt

    if useful_energy_at_1_megawatt is not None:
        filters["useful_energy_at_1_megawatt"] = useful_energy_at_1_megawatt
    
    if efficiency is not None:
        filters["efficiency"] = efficiency

    if installation_date_from is not None:
        filters["installation_date__gte"] = installation_date_from
        
    if installation_date_to is not None:
        filters["installation_date__lte"] = installation_date_to

    sites_data = await site_crud.get_multi(
        db=db,
        offset=compute_offset(page, items_per_page),
        limit=items_per_page,
        sort_columns=[sort_by] if sort_by else [],
        sort_orders=[sort_order] if sort_by else [],
        **filters
    )
    for site in sites_data["data"]:
        if site["country"] == SiteCountry.FRANCE:
            data = await site_france_crud.get(db=db, id=site["id"])
            site["useful_energy_at_1_megawatt"] = data["useful_energy_at_1_megawatt"]
        elif site["country"] == SiteCountry.ITALY:
            data = await site_italy_crud.get(db=db, id=site["id"])
            site["efficiency"] = data["efficiency"]

    response: dict[str, Any] = paginated_response(crud_data=sites_data, page=page, items_per_page=items_per_page)
    return response


@router.get("/{site_id}", response_model=SiteWithGroups)
async def read_site(
    site_id: int = Path(..., title="The ID of the site to get"),
    db: AsyncSession = Depends(get_session),
) -> SiteWithGroups:
    """
    Get a specific site by ID.
    """
    # FastCRUD not working with joined, why?
    # site = await site_crud.get_multi_joined(
    #     db=db,
    #     id=site_id,
    #     schema_to_select=SiteRead,
    #     joins_config=joins_config
    # )
    result = await db.execute(
        select(SiteModel).options(selectinload(SiteModel.groups)).where(SiteModel.id == site_id)
    )
    site = result.unique().scalar_one_or_none()
    if site.country == SiteCountry.FRANCE:
        data = await site_france_crud.get(db=db, id=site.id)
        site.useful_energy_at_1_megawatt = data["useful_energy_at_1_megawatt"]
    elif site.country == SiteCountry.ITALY:
        data = await site_italy_crud.get(db=db, id=site.id)
        site.efficiency = data["efficiency"]
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site



@router.post("/france", response_model=SiteRead, status_code=201)
async def create_site_france(
    site: SiteFranceCreate,
    db: AsyncSession = Depends(get_session),
) -> Site:
    """
    Create a new french site.
    """
    if site.installation_date:
        existing_sites = await db.execute(
            select(SiteFrance).where(SiteFrance.installation_date == site.installation_date)
        )
        if existing_sites.scalars().first():
            raise HTTPException(
                status_code=422,
                detail="Only one French site can be installed per day"
            )

    return await site_france_crud.create(db=db, object=site)


@router.post("/italy", response_model=SiteRead, status_code=201)
async def create_site_italy(
    site: SiteItalyCreate,
    db: AsyncSession = Depends(get_session),
) -> Site:
    """
    Create a new italian site.
    """
    if site.installation_date:
        weekday = site.installation_date.weekday()
        if weekday < 5:
            raise HTTPException(
                status_code=422,
                detail="Italian sites must be installed on weekends"
            )

    return await site_italy_crud.create(db=db, object=site)


@router.patch("/{site_id}", response_model=SiteRead)
async def update_site(
    site_update: SiteBase,
    site_id: int = Path(..., title="The ID of the site to update"),
    db: AsyncSession = Depends(get_session),
) -> Site:
    """
    Update a site.
    """
    site = await site_crud.get(db=db, id=site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    updated_site = await site_crud.update(
        db=db,
        object=site_update,
        id=site_id,
        return_as_model=True,
        schema_to_select=SiteRead,
    )
    return updated_site


@router.delete("/{site_id}")
async def delete_site(
    site_id: int = Path(..., title="The ID of the site to delete"),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """
    Delete a site.
    """
    site = await site_crud.get(db=db, id=site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    await site_crud.delete(db=db, id=site_id)
    return {"message": "Site deleted successfully"}


@router.post("/{site_id}/groups/{group_id}", status_code=204)
async def add_site_to_group(
    site_id: int = Path(..., title="The ID of the site"),
    group_id: int = Path(..., title="The ID of the group"),
    db: AsyncSession = Depends(get_session),
) -> None:
    """
    Add a site to a group.
    """
    site = await db.execute(
        select(SiteModel).options(joinedload(SiteModel.groups)).where(SiteModel.id == site_id)
    )
    site = site.unique().scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group not in site.groups:
        site.groups.append(group)
        await db.commit()
        await db.refresh(site)
        
    return None

@router.delete("/{site_id}/groups/{group_id}", status_code=204)
async def remove_site_from_group(
    site_id: int = Path(..., title="The ID of the site"),
    group_id: int = Path(..., title="The ID of the group"),
    db: AsyncSession = Depends(get_session),
) -> None:
    """
    Remove a site from a group.
    """
    site = await db.execute(
        select(SiteModel).options(joinedload(SiteModel.groups)).where(SiteModel.id == site_id)
    )
    site = site.unique().scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group in site.groups:
        site.groups.remove(group)
        await db.commit()
        await db.refresh(site)
        
    return None
