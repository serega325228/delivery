from decimal import Decimal
from uuid import UUID

from app.exceptions import (
    CourierNotAllowedError,
    CourierNotFoundError,
    CourierUnavailableError,
    CustomerNotFoundError,
    DeliveryMethodNotSelectedError,
    InvalidStatusTransitionError,
    OrderModificationError,
    OrderNotFoundError,
)
from app.schemas.delivery import DeliveryType, get_delivery_method
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.repositories.courier import CourierRepository
from app.repositories.customer import CustomerRepository
from app.repositories.order import OrderRepository
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.courier import CourierService


_ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CREATED: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.IN_DELIVERY, OrderStatus.CANCELLED},
    OrderStatus.IN_DELIVERY: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        customer_repository: CustomerRepository,
        courier_repository: CourierRepository,
    ) -> None:
        self.orders = order_repository
        self.customers = customer_repository
        self.couriers = courier_repository

    def create_order(self, customer_id: UUID, address: str) -> Order:
        customer = self.customers.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError(customer_id)
        order = self.orders.create(customer_id, address)
        order = self.find_courier(order)
        self._commit()
        return order

    def get_order(self, order_id: UUID) -> Order:
        order = self.orders.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(order_id)
        return order

    def get_orders(self) -> list[Order]:
        return self.orders.get_all()

    def add_item(self, order_id: UUID, item: OrderItem) -> Order:
        order = self.get_order(order_id)
        self._ensure_created(order, "Добавлять позиции можно только в созданный заказ")
        order.items.append(item)
        self._commit()
        return order

    def set_delivery_method(self, order_id: UUID, delivery_type: DeliveryType) -> Order:
        order = self.get_order(order_id)
        self._ensure_created(order, "Менять способ доставки можно только у созданного заказа")
        if order.courier:
            raise OrderModificationError("Нельзя менять доставку после назначения курьера")
        delivery_method = get_delivery_method(delivery_type)
        order.delivery_type = delivery_method.delivery_type.value
        order.delivery_cost = delivery_method.calculate_cost(order)
        order.delivery_eta = delivery_method.estimate_delivery_time(order)
        self._commit()
        return order

    def find_courier(self, order: Order) -> Order:
        if order.status not in {OrderStatus.CREATED, OrderStatus.CONFIRMED}:
            raise CourierNotAllowedError("Курьера нельзя назначить на этом этапе заказа")
        if not order.delivery_type:
            raise DeliveryMethodNotSelectedError()
        if not get_delivery_method(order.delivery_type).requires_courier(): #think about implementation of delivery
            raise CourierNotAllowedError("Для самовывоза курьер не нужен")
        if order.courier:
            raise CourierNotAllowedError("Курьер уже назначен")
        courier = self.couriers.get_available()
        if not courier:
            raise CourierUnavailableError("Нет доступных курьеров")
        CourierService.reserve(courier)
        order.courier = courier
        self._commit()
        return order

    def change_status(self, order_id: UUID, new_status: OrderStatus) -> Order:
        order = self.get_order(order_id)
        current_status = OrderStatus(order.status)
        new_status = OrderStatus(new_status)
        if new_status not in _ALLOWED_TRANSITIONS[current_status]:
            raise InvalidStatusTransitionError(
                f"Недопустимый переход: {current_status.value} -> {new_status.value}"
            )
        if new_status == OrderStatus.CONFIRMED:
            if not order.items:
                raise OrderModificationError("Нельзя подтвердить заказ без позиций")
            if not order.delivery_type:
                raise DeliveryMethodNotSelectedError()
        if new_status == OrderStatus.IN_DELIVERY:
            if not order.delivery_type:
                raise DeliveryMethodNotSelectedError()
            if get_delivery_method(order.delivery_type).requires_courier() and not order.courier:
                raise CourierNotAllowedError("Перед отправкой назначьте курьера")
        order.status = new_status.value
        if new_status in {OrderStatus.DELIVERED, OrderStatus.CANCELLED} and order.courier:
            CourierService.release(order.courier)
        self._commit()
        return order

    @staticmethod
    def calculate_goods_cost(order: Order) -> Decimal:
        return sum((item.total for item in order.items), Decimal("0.00"))

    @staticmethod
    def calculate_total_cost(order: Order) -> Decimal:
        return OrderService.calculate_goods_cost(order) + order.delivery_cost

    @staticmethod
    def _ensure_created(order: Order, message: str) -> None:
        if order.status != OrderStatus.CREATED:
            raise OrderModificationError(message)

    def _commit(self) -> None:
        try:
            self.orders.commit()
        except Exception:
            self.orders.rollback()
            raise
