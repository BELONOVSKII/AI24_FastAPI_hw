from fastapi import FastAPI

from app.auth.auth import router as auth_router
from app.db import Base, engine
from app.routers.links import router as link_router

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(auth_router)
app.include_router(link_router)
