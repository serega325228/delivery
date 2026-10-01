from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.orm.session import Session

from app.database import get_session, init_db
from app.repositories.courier import CourierRepository
from app.repositories.order import OrderRepository
from app.routers import couriers, customers, orders
from app.services.courier import CourierService
from app.services.customer import CustomerRepository, CustomerService
from app.services.order import OrderService


# repositories
def get_courier_repository(
    session: Session = Depends(get_session),
) -> CourierRepository:
    return CourierRepository(session)


def get_customer_repository(
    session: Session = Depends(get_session),
) -> CustomerRepository:
    return CustomerRepository(session)


def get_order_repository(session: Session = Depends(get_session)) -> OrderRepository:
    return OrderRepository(session)


# services
def get_courier_service(
    couriers: CourierRepository = Depends(get_courier_repository),
) -> CourierService:
    return CourierService(couriers)


def get_customer_service(
    customers: CustomerRepository = Depends(get_customer_repository),
) -> CustomerService:
    return CustomerService(customers)


def get_order_service(
    orders: OrderRepository = Depends(get_order_repository),
    customers: CustomerRepository = Depends(get_customer_repository),
    couriers: CourierRepository = Depends(get_courier_repository),
) -> OrderService:
    return OrderService(orders, customers, couriers)


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
