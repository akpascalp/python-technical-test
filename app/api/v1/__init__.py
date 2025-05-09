from fastapi import APIRouter

from .sites import router as sites_router
from .groups import router as groups_router

router = APIRouter(prefix="/v1")

router.include_router(sites_router, prefix="/sites", tags=["sites"])

router.include_router(groups_router, prefix="/groups", tags=["groups"])
