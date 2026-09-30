from uuid import UUID, uuid4
from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), unique=True)
