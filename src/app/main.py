from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import couriers, customers, orders


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="Симулятор службы доставки",
    description="Fake Delivery service API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(customers.router)
app.include_router(couriers.router)
app.include_router(orders.router)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "Delivery service API", "docs": "/docs"}
