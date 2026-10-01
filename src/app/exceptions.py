from uuid import UUID


class DomainError(Exception):
    """Base class for expected business errors"""


class NotFoundError(DomainError):
    """Base class for missing domain entities"""


class CustomerNotFoundError(NotFoundError):
    def __init__(self, customer_id: UUID) -> None:
        super().__init__(f"Клиент с id={customer_id} не найден")


class CourierNotFoundError(NotFoundError):
    def __init__(self, courier_id: UUID) -> None:
        super().__init__(f"Курьер с id={courier_id} не найден")


class OrderNotFoundError(NotFoundError):
    def __init__(self, order_id: UUID) -> None:
        super().__init__(f"Заказ с id={order_id} не найден")


class OrderItemNotFoundError(NotFoundError):
    def __init__(self, item_id: UUID) -> None:
        super().__init__(f"Позиция с id={item_id} не найдена в этом заказе")


class InvalidStatusTransitionError(DomainError):
    """Raised when an order status transition is forbidden"""


class OrderModificationError(DomainError):
    """Raised when an order can no longer be edited"""


class DeliveryMethodNotSelectedError(DomainError):
    def __init__(self) -> None:
        super().__init__("Сначала выберите способ доставки")


class CourierNotAllowedError(DomainError):
    """Raised when a courier cannot be assigned to an order"""


class CourierUnavailableError(DomainError):
    """Raised when a courier is already assigned elsewhere"""
