from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.exceptions import CustomerNotFoundError, DomainError
from app.models.customer import Customer
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate


class CustomerService:
    def __init__(self, customer_repository: CustomerRepository) -> None:
        self.customers = customer_repository

    def create(self, name: str, phone: str) -> Customer:
        data = CustomerCreate(name=name, phone=phone)
        try:
            customer = self.customers.create(data.name, data.phone)
            self.customers.commit()
            return customer
        except IntegrityError as error:
            self.customers.rollback()
            raise DomainError("Клиент с таким телефоном уже существует") from error

    def get(self, customer_id: UUID) -> Customer:
        customer = self.customers.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError(customer_id)
        return customer

    def get_all(self) -> list[Customer]:
        return self.customers.get_all()
