from typing import Any
from enum import Enum

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from fastcrud.paginated import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, with_polymorphic

from infrastructure.db import get_session
from infrastructure.schemas.group import GroupRead, GroupBase
from infrastructure.schemas.site import SiteRead
from infrastructure.crud.crud_groups import group_crud
from infrastructure.models.group import Group, GroupType
from infrastructure.models.site import Site, SiteFrance, SiteItaly
from infrastructure.models.associations import site_group

router = APIRouter()


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


@router.get("/", response_model=PaginatedListResponse[GroupRead])
async def read_groups(
    db: AsyncSession = Depends(get_session),
    page: int = 1,
    items_per_page: int = 10,
    limit: int = 100,
    name: str | None = None,
    type: GroupType | None = None,
    sort_by: str | None = Query(None, description="Field to sort by"),
    sort_order: SortOrder = SortOrder.desc,
) -> dict:
    """
    Get all groups with filtering and sorting options.
    """
    filters = {}

    if name is not None:
        filters["name"] = name

    if type is not None:
        filters["type"] = type

    groups_data = await group_crud.get_multi(
        db=db,
        offset=compute_offset(page, items_per_page),
        limit=items_per_page,
        sort_columns=[sort_by] if sort_by else [],
        sort_orders=[sort_order] if sort_by else [],
        **filters
    )

    response: dict[str, Any] = paginated_response(
        crud_data=groups_data, page=page, items_per_page=items_per_page
    )
    return response


@router.get("/{group_id}", response_model=GroupRead)
async def read_group(
    group_id: int = Path(..., title="The ID of the group to get"),
    db: AsyncSession = Depends(get_session),
) -> Group:
    """
    Get a specific group by ID.
    """
    group = await group_crud.get(db=db, id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.get("/{group_id}/children", response_model=list[GroupRead])
async def read_group_children(
    group_id: int = Path(..., title="The ID of the group to get children for"),
    db: AsyncSession = Depends(get_session),
) -> list[Group]:
    """
    Get all children of a specific group.
    """
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    children = await db.execute(select(Group).where(Group.parent_id == group_id))
    return children.scalars().all()


@router.get("/{group_id}/sites", response_model=list[SiteRead])
async def read_group_sites(
    group_id: int = Path(..., title="The ID of the group to get sites for"),
    db: AsyncSession = Depends(get_session),
) -> list[dict]:
    """
    Get all sites of a specific group.
    """
    result_group = await db.execute(select(Group).where(Group.id == group_id))
    group = result_group.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    PolymorphicSite = with_polymorphic(Site, [SiteFrance, SiteItaly])

    result = await db.execute(
        select(PolymorphicSite)
        .options(selectinload(PolymorphicSite.groups))
        .join(site_group, site_group.c.site_id == PolymorphicSite.id)
        .where(site_group.c.group_id == group_id)
    )
    
    sites = result.unique().scalars().all()

    site_dicts = []
    for site in sites:
        site_dict = {
            "id": site.id,
            "name": site.name,
            "installation_date": site.installation_date,
            "max_power_megawatt": site.max_power_megawatt,
            "min_power_megawatt": site.min_power_megawatt,
            "country": site.country,
            "groups": [{"id": g.id, "name": g.name, "type": g.type} for g in site.groups],
            "efficiency": None,
            "useful_energy_at_1_megawatt": None,
        }

        if isinstance(site, SiteFrance):
            site_dict["useful_energy_at_1_megawatt"] = site.useful_energy_at_1_megawatt
        elif isinstance(site, SiteItaly):
            site_dict["efficiency"] = site.efficiency
        
        site_dicts.append(site_dict)
    
    return site_dicts


@router.post("/", response_model=GroupRead, status_code=201)
async def create_group(group: GroupBase, db: AsyncSession = Depends(get_session)) -> Group:
    """
    Create a new group.
    """
    # TODO verify group creation rules
    return await group_crud.create(db=db, object=group)


@router.patch("/{group_id}", response_model=GroupRead)
async def update_group(
    group_update: GroupBase,
    group_id: int = Path(..., title="The ID of the group to update"),
    db: AsyncSession = Depends(get_session),
) -> Group:
    """
    Update a group.
    """
    group = await group_crud.get(db=db, id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    updated_group = await group_crud.update(
        db=db, object=group_update, id=group_id, return_as_model=True, schema_to_select=GroupRead
    )
    return updated_group


@router.delete("/{group_id}")
async def delete_group(
    group_id: int = Path(..., title="The ID of the group to delete"),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """
    Delete a group.
    """
    group = await group_crud.get(db=db, id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    await group_crud.delete(db=db, id=group_id)
    return {"message": "Group deleted successfully"}


@router.post("/{parent_id}/children/{child_id}", status_code=204)
async def add_child_to_group(
    parent_id: int = Path(..., title="The ID of the parent group"),
    child_id: int = Path(..., title="The ID of the child group to add"),
    db: AsyncSession = Depends(get_session),
) -> None:
    """
    Add a child group to a parent group.
    """
    parent = await db.get(Group, parent_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Parent group not found")

    child = await db.get(Group, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child group not found")

    if parent_id == child_id:
        raise HTTPException(status_code=422, detail="A group cannot be its own child")

    current = parent
    while current and current.parent_id:
        if current.parent_id == child_id:
            raise HTTPException(
                status_code=422,
                detail="Creating this relationship would introduce a cycle in the hierarchy",
            )
        current = await db.get(Group, current.parent_id)

    child.parent_id = parent_id
    await db.commit()
    return None


@router.delete("/{parent_id}/children/{child_id}", status_code=204)
async def remove_child_from_group(
    parent_id: int = Path(..., title="The ID of the parent group"),
    child_id: int = Path(..., title="The ID of the child group to remove"),
    db: AsyncSession = Depends(get_session),
) -> None:
    """
    Remove a child group from a parent group.
    """
    child = await db.get(Group, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child group not found")

    if child.parent_id != parent_id:
        raise HTTPException(
            status_code=422, detail="This group is not a child of the specified parent"
        )

    child.parent_id = None
    await db.commit()
    return None
