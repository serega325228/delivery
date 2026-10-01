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
        orders = self.session.scalars(self._query().order_by(Order.created_at.desc(), Order.id)).all()
        return list(orders)

    def get_by_customer(self, customer_id: UUID) -> list[Order]:
        return list(self.session.scalars(
            self._query()
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc(), Order.id)
        ).all())

    def get_latest_by_customer(self, customer_id: UUID) -> Order | None:
        return self.session.scalar(
            self._query()
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc(), Order.id)
            .limit(1)
        )

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
