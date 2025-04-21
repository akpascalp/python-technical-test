from fastapi import APIRouter

from .sites import router as sites_router

router = APIRouter(prefix="/v1")

router.include_router(
    sites_router,
    prefix="/sites",
    tags=["sites"],
)
