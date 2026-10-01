from decimal import Decimal
from uuid import UUID

from app.exceptions import (
    CourierUnavailableError,
    CustomerNotFoundError,
    DeliveryMethodNotSelectedError,
    InvalidStatusTransitionError,
    OrderItemNotFoundError,
    OrderModificationError,
    OrderNotFoundError,
)
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.repositories.courier import CourierRepository
from app.repositories.customer import CustomerRepository
from app.repositories.order import OrderRepository
from app.schemas.delivery import DeliveryType, get_delivery_method
from app.schemas.order import OrderItemCreate, OrderReq
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
        data = OrderReq(customer_id=customer_id, address=address)
        customer = self.customers.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError(customer_id)
        order = self.orders.create(customer_id, data.address)
        self._commit()
        return order

    def get_order(self, order_id: UUID) -> Order:
        order = self.orders.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(order_id)
        return order

    def get_orders(self) -> list[Order]:
        return self.orders.get_all()

    def get_customer_orders(self, customer_id: UUID) -> list[Order]:
        if not self.customers.get_by_id(customer_id):
            raise CustomerNotFoundError(customer_id)
        return self.orders.get_by_customer(customer_id)

    def get_latest_order(self, customer_id: UUID) -> Order | None:
        if not self.customers.get_by_id(customer_id):
            raise CustomerNotFoundError(customer_id)
        return self.orders.get_latest_by_customer(customer_id)

    def add_item(self, order_id: UUID, item: OrderItem) -> Order:
        order = self.get_order(order_id)
        self._ensure_created(order, "Добавлять позиции можно только в созданный заказ")
        data = OrderItemCreate(name=item.name, quantity=item.quantity, price=item.price)
        item.name, item.quantity, item.price = data.name, data.quantity, data.price
        order.items.append(item)
        self._commit()
        return order

    def remove_item(self, order_id: UUID, item_id: UUID) -> Order:
        order = self.get_order(order_id)
        self._ensure_created(order, "Удалять позиции можно только из созданного заказа")
        item = next((item for item in order.items if item.id == item_id), None)
        if item is None:
            raise OrderItemNotFoundError(item_id)
        order.items.remove(item)
        self._commit()
        return order

    def set_delivery_method(self, order_id: UUID, delivery_type: DeliveryType) -> Order:
        order = self.get_order(order_id)
        self._ensure_created(
            order, "Менять способ доставки можно только у созданного заказа"
        )
        if not order.items:
            raise OrderModificationError("Сначала добавьте позиции в заказ")
        delivery_method = get_delivery_method(delivery_type)
        courier = None
        if delivery_method.requires_courier():
            required_capacity = sum(item.quantity for item in order.items)
            courier = self.couriers.get_available(required_capacity)
            if not courier:
                raise CourierUnavailableError(
                    "Все курьеры заняты или нет курьера нужной вместимости. "
                    "Выберите самовывоз или подождите курьера и попробуйте снова."
                )
            try:
                CourierService(self.couriers).reserve(courier)
            except CourierUnavailableError:
                self.orders.rollback()
                raise
        order.delivery_type = delivery_method.delivery_type.value
        order.delivery_cost = delivery_method.calculate_cost(order)
        order.delivery_eta = delivery_method.estimate_delivery_time(order)
        order.courier = courier
        order.status = OrderStatus.CONFIRMED.value
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
            if (
                get_delivery_method(order.delivery_type).requires_courier()
                and not order.courier
            ):
                raise OrderModificationError("Перед отправкой назначьте курьера")
        order.status = new_status.value
        if (
            new_status in {OrderStatus.DELIVERED, OrderStatus.CANCELLED}
            and order.courier
        ):
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
    def can_edit(order: Order) -> bool:
        return order.status == OrderStatus.CREATED and order.courier is None

    @staticmethod
    def _ensure_created(order: Order, message: str) -> None:
        if not OrderService.can_edit(order):
            raise OrderModificationError(message)

    def _commit(self) -> None:
        try:
            self.orders.commit()
        except Exception:
            self.orders.rollback()
            raise
