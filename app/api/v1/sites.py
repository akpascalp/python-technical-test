from datetime import date
from typing import Any
from enum import Enum

from fastapi import APIRouter, Depends, Query
from fastcrud.paginated import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db import get_session
from infrastructure.schemas.site import SiteRead
from infrastructure.crud.crud_sites import site_crud

router = APIRouter()

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

@router.get("/", response_model=PaginatedListResponse[SiteRead])
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
    userful_energy_at_1_megawatt: float | None = None,
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

    if userful_energy_at_1_megawatt is not None:
        filters["userful_energy_at_1_megawatt"] = userful_energy_at_1_megawatt

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

    response: dict[str, Any] = paginated_response(crud_data=sites_data, page=page, items_per_page=items_per_page)
    return response
