from typing import Any
from enum import Enum

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from fastcrud.paginated import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db import get_session
from infrastructure.schemas.group import GroupRead, GroupBase
from infrastructure.crud.crud_groups import group_crud
from infrastructure.models.group import Group, GroupType

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

    response: dict[str, Any] = paginated_response(crud_data=groups_data, page=page, items_per_page=items_per_page)
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



@router.post("/", response_model=GroupRead, status_code=201)
async def create_group(
    group: GroupBase,
    db: AsyncSession = Depends(get_session),
) -> Group:
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
        db=db,
        object=group_update,
        id=group_id,
        return_as_model=True,
        schema_to_select=GroupRead,
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
