from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.order import Order


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, customer_id: UUID, address: str) -> Order:
        order = Order(customer_id=customer_id, address=address)
        self.session.add(order)
        self.session.flush()
        return order

    def get_by_id(self, order_id: UUID) -> Order | None:
        order = self.session.scalar(self._query().where(Order.id == order_id))
        return order

    def get_all(self) -> list[Order]:
        orders = self.session.scalars(self._query().order_by(Order.id)).all()
        return list(orders)

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    @staticmethod
    def _query():
        return select(Order).options(
            joinedload(Order.customer),
            joinedload(Order.courier),
            selectinload(Order.items),
        )
