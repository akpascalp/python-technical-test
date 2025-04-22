from fastapi import FastAPI

from api.v1 import router as api_v1_router

app = FastAPI(title="Python technical test")

app.include_router(api_v1_router, prefix="/api")


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint returning API information.
    """
    return {"message": "Welcome to the API", "docs": "/docs", "redoc": "/redoc"}
