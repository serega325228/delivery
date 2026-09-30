from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from app.database import Base
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from app.exceptions import (
    CourierNotAllowedError,
    DeliveryMethodNotSelectedError,
    InvalidStatusTransitionError,
    OrderModificationError,
)
from app.models.courier import Courier
from app.models.customer import Customer
from app.schemas.delivery import DeliveryMethod, DeliveryType
from app.models.order_item import OrderItem
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.sqltypes import Numeric, String


class OrderStatus(str, Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    IN_DELIVERY = "in_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


_ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CREATED: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.IN_DELIVERY, OrderStatus.CANCELLED},
    OrderStatus.IN_DELIVERY: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id"))
    address: Mapped[str] = mapped_column(String(300))
    delivery_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    delivery_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    delivery_eta: Mapped[str | None] = mapped_column(String(100), nullable=True)
    courier_id: Mapped[UUID | None] = mapped_column(ForeignKey("couriers.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="created")

    customer: Mapped[Customer] = relationship()
    courier: Mapped[Courier | None] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    # @classmethod
    # def restore(
    #     cls,
    #     *,
    #     id: int,
    #     customer: Customer,
    #     address: str,
    #     items: list[OrderItem],
    #     delivery_method: DeliveryMethod | None,
    #     delivery_cost: Decimal,
    #     delivery_eta: str | None,
    #     courier: Courier | None,
    #     status: OrderStatus,
    # ) -> "Order":
    #     order = cls(id=id, customer=customer, address=address)
    #     order._items = list(items)
    #     order._delivery_method = delivery_method
    #     order._delivery_cost = delivery_cost
    #     order._delivery_eta = delivery_eta
    #     order._courier = courier
    #     order._status = status
    #     return order

    # @property
    # def items(self) -> list[OrderItem]:
    #     return list(self._items)

    # @property
    # def delivery_method(self) -> DeliveryMethod | None:
    #     return self._delivery_method

    # @property
    # def delivery_type(self) -> DeliveryType | None:
    #     return self._delivery_method.delivery_type if self._delivery_method else None

    # @property
    # def delivery_cost(self) -> Decimal:
    #     return self._delivery_cost

    # @property
    # def delivery_eta(self) -> str | None:
    #     return self._delivery_eta

    # @property
    # def courier(self) -> Courier | None:
    #     return self._courier

    # @property
    # def status(self) -> OrderStatus:
    #     return self._status

    # @property
    # def goods_cost(self) -> Decimal:
    #     return sum((item.total for item in self._items), Decimal("0.00"))

    # @property
    # def total_cost(self) -> Decimal:
    #     return self.goods_cost + self.delivery_cost

    # def add_item(self, item: OrderItem) -> None:
    #     self._ensure_created("Добавлять позиции можно только в созданный заказ")
    #     self._items.append(item)

    # def set_delivery_method(self, delivery_method: DeliveryMethod) -> None:
    #     self._ensure_created("Менять способ доставки можно только у созданного заказа")
    #     if self._courier:
    #         raise OrderModificationError("Нельзя менять доставку после назначения курьера")
    #     self._delivery_method = delivery_method
    #     self._delivery_cost = delivery_method.calculate_cost(self)
    #     self._delivery_eta = delivery_method.estimate_delivery_time(self)

    # def assign_courier(self, courier: Courier) -> None:
    #     if self._status not in {OrderStatus.CREATED, OrderStatus.CONFIRMED}:
    #         raise CourierNotAllowedError("Курьера нельзя назначить на этом этапе заказа")
    #     if not self._delivery_method:
    #         raise DeliveryMethodNotSelectedError()
    #     if not self._delivery_method.requires_courier():
    #         raise CourierNotAllowedError("Для самовывоза курьер не нужен")
    #     if self._courier:
    #         raise CourierNotAllowedError("Курьер уже назначен")
    #     courier.reserve()
    #     self._courier = courier

    # def change_status(self, new_status: OrderStatus) -> None:
    #     if new_status not in _ALLOWED_TRANSITIONS[self._status]:
    #         raise InvalidStatusTransitionError(
    #             f"Недопустимый переход: {self._status.value} -> {new_status.value}"
    #         )
    #     if new_status == OrderStatus.CONFIRMED:
    #         if not self._items:
    #             raise OrderModificationError("Нельзя подтвердить заказ без позиций")
    #         if not self._delivery_method:
    #             raise DeliveryMethodNotSelectedError()
    #     if new_status == OrderStatus.IN_DELIVERY:
    #         if not self._delivery_method:
    #             raise DeliveryMethodNotSelectedError()
    #         if self._delivery_method.requires_courier() and not self._courier:
    #             raise CourierNotAllowedError("Перед отправкой назначьте курьера")
    #     self._status = new_status
    #     if new_status in {OrderStatus.DELIVERED, OrderStatus.CANCELLED} and self._courier:
    #         self._courier.release()

    # def _ensure_created(self, message: str) -> None:
    #     if self._status != OrderStatus.CREATED:
    #         raise OrderModificationError(message)
