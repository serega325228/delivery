from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException

from app.exceptions import DomainError, NotFoundError
from app.main import get_order_service
from app.schemas.order import (
    DeliveryMethodUpdate,
    OrderItemCreate,
    OrderReq,
    OrderRes,
    StatusUpdate,
)
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])

Orders = Annotated[OrderService, Depends(get_order_service)]


@router.post("", response_model=OrderRes, status_code=status.HTTP_201_CREATED)
async def create_order(request: OrderReq, orders: Orders) -> OrderRes:
    try:
        order = orders.create_order(request.customer_id, request.address)
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return OrderRes.from_domain(order)


@router.get("", response_model=list[OrderRes])
async def get_orders(orders: Orders) -> list[OrderRes]:
    try:
        all_orders = orders.get_orders()
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return [OrderRes.from_domain(order) for order in all_orders]


@router.get("/{order_id}", response_model=OrderRes)
async def get_order(order_id: UUID, orders: Orders) -> OrderRes:
    try:
        order = orders.get_order(order_id)
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return OrderRes.from_domain(order)


@router.post("/{order_id}/items", response_model=OrderRes)
async def add_item(order_id: UUID, data: OrderItemCreate, orders: Orders) -> OrderRes:
    try:
        order = orders.add_item(order_id, data.to_domain())
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return OrderRes.from_domain(order)


@router.put("/{order_id}/delivery", response_model=OrderRes)
async def set_delivery(
    order_id: UUID, data: DeliveryMethodUpdate, orders: Orders
) -> OrderRes:
    try:
        order = orders.set_delivery_method(order_id, data.delivery_type)
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return OrderRes.from_domain(order)


# @router.put("/{order_id}/courier", response_model=OrderRes)
# async def assign_courier(
#     order_id: UUID, data: CourierAssignment, orders: Orders
# ) -> OrderRes:
#     try:
#         order = orders.assign_courier(order_id, data.courier_id)
#     except NotFoundError as error:
#         raise HTTPException(status_code=404, detail=str(error)) from error
#     except DomainError as error:
#         raise HTTPException(status_code=409, detail=str(error)) from error
#     return OrderRes.from_domain(order)


@router.put("/{order_id}/status", response_model=OrderRes)
async def change_status(order_id: UUID, data: StatusUpdate, orders: Orders) -> OrderRes:
    try:
        order = orders.change_status(order_id, data.status)
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return OrderRes.from_domain(order)
