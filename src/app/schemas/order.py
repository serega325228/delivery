from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.schemas.courier import CourierRes
from app.schemas.customer import CustomerRes
from app.schemas.delivery import DeliveryType


class OrderReq(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: UUID
    address: str = Field(min_length=5, max_length=300)


class OrderItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(gt=0)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)

    def to_domain(self) -> OrderItem:
        return OrderItem(name=self.name, quantity=self.quantity, price=self.price)


class OrderItemRead(BaseModel):
    id: UUID
    name: str
    quantity: int
    price: Decimal

    @computed_field
    @property
    def total(self) -> Decimal:
        return self.price * self.quantity


class DeliveryMethodUpdate(BaseModel):
    delivery_type: DeliveryType


class StatusUpdate(BaseModel):
    status: OrderStatus


class OrderRes(BaseModel):
    id: UUID
    customer: CustomerRes
    created_at: datetime
    address: str
    items: list[OrderItemRead]
    goods_cost: Decimal
    delivery_method: DeliveryType | None
    delivery_cost: Decimal
    delivery_eta: str | None
    courier: CourierRes | None
    editable: bool
    status: OrderStatus
    total_cost: Decimal

    @classmethod
    def from_domain(cls, order: Order) -> "OrderRes":
        from app.services.order import OrderService

        return cls(
            id=order.id,
            customer=CustomerRes.from_domain(order.customer),
            created_at=order.created_at,
            address=order.address,
            items=[
                OrderItemRead.model_validate(item, from_attributes=True)
                for item in order.items
            ],
            goods_cost=OrderService.calculate_goods_cost(order),
            delivery_method=order.delivery_type,
            delivery_cost=order.delivery_cost,
            delivery_eta=order.delivery_eta,
            courier=CourierRes.from_domain(order.courier) if order.courier else None,
            editable=OrderService.can_edit(order),
            status=order.status,
            total_cost=OrderService.calculate_total_cost(order),
        )
