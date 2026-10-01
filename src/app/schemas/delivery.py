from abc import ABC, abstractmethod
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from app.models.order import Order


class DeliveryType(str, Enum):
    STANDARD = "standard"
    EXPRESS = "express"
    PICKUP = "pickup"


class DeliveryMethod(ABC):
    delivery_type: ClassVar[DeliveryType]

    @abstractmethod
    def calculate_cost(self, order: "Order") -> Decimal:
        raise NotImplementedError

    @abstractmethod
    def estimate_delivery_time(self, order: "Order") -> str:
        raise NotImplementedError

    @abstractmethod
    def requires_courier(self) -> bool:
        raise NotImplementedError


class StandardDelivery(DeliveryMethod):
    delivery_type = DeliveryType.STANDARD

    def calculate_cost(self, order: "Order") -> Decimal:
        return Decimal("300.00")

    def estimate_delivery_time(self, order: "Order") -> str:
        return "2–3 дня"

    def requires_courier(self) -> bool:
        return True


class ExpressDelivery(DeliveryMethod):
    delivery_type = DeliveryType.EXPRESS

    def calculate_cost(self, order: "Order") -> Decimal:
        return Decimal("600.00")

    def estimate_delivery_time(self, order: "Order") -> str:
        return "1 день"

    def requires_courier(self) -> bool:
        return True


class PickupDelivery(DeliveryMethod):
    delivery_type = DeliveryType.PICKUP

    def calculate_cost(self, order: "Order") -> Decimal:
        return Decimal("0.00")

    def estimate_delivery_time(self, order: "Order") -> str:
        return "можно забрать сегодня"

    def requires_courier(self) -> bool:
        return False


_DELIVERY_METHODS: dict[DeliveryType, type[DeliveryMethod]] = {
    DeliveryType.STANDARD: StandardDelivery,
    DeliveryType.EXPRESS: ExpressDelivery,
    DeliveryType.PICKUP: PickupDelivery,
}


def get_delivery_method(delivery_type: DeliveryType | str) -> DeliveryMethod:
    return _DELIVERY_METHODS[DeliveryType(delivery_type)]()
