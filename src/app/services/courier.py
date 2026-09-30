from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.exceptions import CourierNotFoundError, CourierUnavailableError, DomainError
from app.models.courier import Courier
from app.repositories.courier import CourierRepository
from app.schemas.courier import CourierCreate


class CourierService:
    def __init__(self, courier_repository: CourierRepository) -> None:
        self.couriers = courier_repository

    def create(self, name: str, phone: str) -> Courier:
        data = CourierCreate(name=name, phone=phone)
        try:
            courier = self.couriers.create(data.name, data.phone)
            self.couriers.commit()
            return courier
        except IntegrityError as error:
            self.couriers.rollback()
            raise DomainError("Курьер с таким телефоном уже существует") from error

    def get(self, courier_id: UUID) -> Courier:
        courier = self.couriers.get_by_id(courier_id)
        if not courier:
            raise CourierNotFoundError(courier_id)
        return courier

    def get_all(self) -> list[Courier]:
        return self.couriers.get_all()

    @staticmethod
    def reserve(courier: Courier) -> None:
        if not courier.available:
            raise CourierUnavailableError(f"Курьер {courier.name} сейчас занят")
        courier.available = False

    @staticmethod
    def release(courier: Courier) -> None:
        courier.available = True
