from uuid import UUID, uuid4

from app.database import Base

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.sqltypes import Boolean, String


class Courier(Base):
    __tablename__ = "couriers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
