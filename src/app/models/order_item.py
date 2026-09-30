from decimal import Decimal
from uuid import UUID, uuid4

from app.database import Base
from app.models.order import Order
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.sqltypes import Numeric, String

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    order: Mapped[Order] = relationship(back_populates="items")

    @property
    def total(self) -> Decimal:
        return self.price * self.quantity
