from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.searches import router as searches_router
from app.api.listings import router as listings_router
from app.api.dashboard import router as dashboard_router
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="AutoDeals API",
    description="Car sourcing tool for Dutch dealers",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(searches_router)
app.include_router(listings_router)
app.include_router(dashboard_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
