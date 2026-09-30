from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from app.database import Base
from app.models.courier import Courier
from app.models.customer import Customer
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
