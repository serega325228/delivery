from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.courier import Courier


class CourierRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, name: str, phone: str) -> Courier:
        courier = Courier(name=name, phone=phone)
        self.session.add(courier)
        self.session.flush()
        return courier

    def get_by_id(self, courier_id: UUID) -> Courier | None:
        courier = self.session.get(Courier, courier_id)
        return courier

    def get_all(self) -> list[Courier]:
        couriers = self.session.scalars(select(Courier).order_by(Courier.id)).all()
        return list(couriers)

    def get_available(self) -> Courier | None:
        stmt = select(Courier).where(Courier.available == True).limit(1)
        courier = self.session.scalar(stmt)
        return courier

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
