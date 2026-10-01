from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.repositories.courier import CourierRepository
from app.repositories.customer import CustomerRepository
from app.repositories.order import OrderRepository
from app.services.courier import CourierService
from app.services.customer import CustomerService
from app.services.order import OrderService


async def get_courier_repository(session: Session = Depends(get_session)) -> CourierRepository:
    return CourierRepository(session)


async def get_customer_repository(session: Session = Depends(get_session)) -> CustomerRepository:
    return CustomerRepository(session)


async def get_order_repository(session: Session = Depends(get_session)) -> OrderRepository:
    return OrderRepository(session)


async def get_courier_service(
    couriers: CourierRepository = Depends(get_courier_repository),
) -> CourierService:
    return CourierService(couriers)


async def get_customer_service(
    customers: CustomerRepository = Depends(get_customer_repository),
) -> CustomerService:
    return CustomerService(customers)


async def get_order_service(
    orders: OrderRepository = Depends(get_order_repository),
    customers: CustomerRepository = Depends(get_customer_repository),
    couriers: CourierRepository = Depends(get_courier_repository),
) -> OrderService:
    return OrderService(orders, customers, couriers)
