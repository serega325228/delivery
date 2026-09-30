from uuid import UUID, uuid4

from app.database import Base

from app.exceptions import CourierUnavailableError
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.sqltypes import Boolean, String, Uuid


class Courier(Base):
    __tablename__ = "couriers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)

    def reserve(self) -> None:
        if not self.available:
            raise CourierUnavailableError(f"Курьер {self.name} сейчас занят")
        self.available = False

    def release(self) -> None:
        self.available = True
