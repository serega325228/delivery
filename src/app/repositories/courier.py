from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.courier import Courier


class CourierRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, name: str, phone: str, capacity: int = 10) -> Courier:
        courier = Courier(name=name, phone=phone, capacity=capacity)
        self.session.add(courier)
        self.session.flush()
        return courier

    def get_by_id(self, courier_id: UUID) -> Courier | None:
        courier = self.session.get(Courier, courier_id)
        return courier

    def get_all(self) -> list[Courier]:
        couriers = self.session.scalars(select(Courier).order_by(Courier.id)).all()
        return list(couriers)

    def get_available(self, required_capacity: int) -> Courier | None:
        stmt = (
            select(Courier)
            .where(Courier.available.is_(True), Courier.capacity >= required_capacity)
            .order_by(Courier.capacity, Courier.id)
            .limit(1)
        )
        courier = self.session.scalar(stmt)
        return courier

    def reserve(self, courier_id: UUID) -> bool:
        result = self.session.execute(
            update(Courier)
            .where(Courier.id == courier_id, Courier.available.is_(True))
            .values(available=False)
        )
        return result.rowcount == 1

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
