from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, name: str, phone: str) -> Customer:
        customer = Customer(name=name, phone=phone)
        self.session.add(customer)
        self.session.flush()
        return customer

    def get_by_id(self, customer_id: UUID) -> Customer | None:
        customer = self.session.get(Customer, customer_id)
        return customer

    def get_all(self) -> list[Customer]:
        customers = self.session.scalars(select(Customer).order_by(Customer.id)).all()
        return list(customers)

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
