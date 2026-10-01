from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.delivery import DeliveryType
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.schemas.courier import CourierRead
from app.schemas.customer import CustomerRead


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
    name: str
    quantity: int
    price: Decimal

    @computed_field
    @property
    def total(self) -> Decimal:
        return self.price * self.quantity


class DeliveryMethodUpdate(BaseModel):
    delivery_type: DeliveryType


class CourierAssignment(BaseModel):
    courier_id: UUID


class StatusUpdate(BaseModel):
    status: OrderStatus


class OrderRes(BaseModel):
    id: UUID
    customer: CustomerRead
    address: str
    items: list[OrderItemRead]
    goods_cost: Decimal
    delivery_method: DeliveryType | None
    delivery_cost: Decimal
    delivery_eta: str | None
    courier: CourierRead | None
    status: OrderStatus
    total_cost: Decimal

    @classmethod
    def from_domain(cls, order: Order) -> "OrderRes":
        from app.services.order import OrderService

        return cls(
            id=order.id,
            customer=CustomerRead.from_domain(order.customer),
            address=order.address,
            items=[OrderItemRead.model_validate(item, from_attributes=True) for item in order.items],
            goods_cost=OrderService.calculate_goods_cost(order),
            delivery_method=order.delivery_type,
            delivery_cost=order.delivery_cost,
            delivery_eta=order.delivery_eta,
            courier=CourierRead.from_domain(order.courier) if order.courier else None,
            status=order.status,
            total_cost=OrderService.calculate_total_cost(order),
        )
