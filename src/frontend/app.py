import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests
import streamlit as st
from pydantic import BaseModel, ValidationError

from app.schemas.courier import CourierReq, CourierRes
from app.schemas.customer import CustomerReq, CustomerRes
from app.schemas.order import DeliveryMethodUpdate, OrderItemCreate, OrderReq, OrderRes

API_URL = os.getenv("DELIVERY_API_URL", "http://127.0.0.1:8000").rstrip("/")
DELIVERY_LABELS = {
    "standard": "Обычная доставка — 300 ₽, 2–3 дня",
    "express": "Экспресс — 600 ₽, 1 день",
    "pickup": "Самовывоз — бесплатно, сегодня",
}
STATUS_LABELS = {
    "created": "Создан, можно редактировать",
    "confirmed": "Подтверждён",
    "in_delivery": "В доставке",
    "delivered": "Доставлен",
    "cancelled": "Отменён",
}


def api(method: str, path: str, data: BaseModel | None = None, **kwargs: Any) -> Any:
    try:
        response = requests.request(
            method,
            f"{API_URL}{path}",
            json=data.model_dump(mode="json") if data else None,
            timeout=5,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        detail = "Сервис недоступен. Проверьте, что FastAPI запущен."
        if error.response is not None:
            try:
                detail = error.response.json().get("detail", error.response.text)
                if isinstance(detail, list):
                    detail = "; ".join(item["msg"] for item in detail)
            except ValueError:
                detail = error.response.text
        raise RuntimeError(detail) from error


def save(method: str, path: str, data: BaseModel | None = None) -> None:
    api(method, path, data)
    st.session_state["notice"] = "Изменения сохранены"
    st.rerun()


def show_order(order: OrderRes) -> None:
    st.write(f"Заказ {order.id}")
    st.write(f"Адрес: {order.address}")
    st.write(f"Статус: {STATUS_LABELS[order.status.value]}")
    if order.items:
        st.dataframe(
            [
                {
                    "Товар": item.name,
                    "Количество": item.quantity,
                    "Цена, ₽": str(item.price),
                    "Сумма, ₽": str(item.total),
                }
                for item in order.items
            ],
            hide_index=True,
        )
    else:
        st.info("В заказе пока нет позиций")
    goods, delivery, total = st.columns(3)
    goods.metric("Товары", f"{order.goods_cost:.2f} ₽")
    delivery.metric("Доставка", f"{order.delivery_cost:.2f} ₽")
    total.metric("Итого", f"{order.total_cost:.2f} ₽")
    if order.delivery_method:
        st.write(DELIVERY_LABELS[order.delivery_method.value])
        st.write(f"Срок: {order.delivery_eta}")
    if order.courier:
        st.write(f"Курьер: {order.courier.name}, {order.courier.phone}")


def client_panel() -> None:
    customer = st.session_state.get("customer")
    if customer is None:
        st.subheader("Вход клиента")
        st.caption("Введите имя и телефон. Если вы здесь впервые, клиент будет создан.")
        with st.form("login"):
            name = st.text_input("Имя", key="login_name")
            phone = st.text_input("Телефон", key="login_phone")
            if st.form_submit_button("Войти"):
                response = api(
                    "POST", "/customers/login", CustomerReq(name=name, phone=phone)
                )
                st.session_state["customer"] = CustomerRes.model_validate(response)
                st.rerun()
        return

    st.write(f"Клиент: {customer.name}, {customer.phone}")
    if st.button("Выйти из клиента"):
        st.session_state.clear()
        st.rerun()

    with st.form("create_order", clear_on_submit=True):
        address = st.text_input("Адрес доставки")
        if st.form_submit_button("Создать заказ"):
            save("POST", "/orders", OrderReq(customer_id=customer.id, address=address))

    st.subheader("Последний заказ")
    if st.button("Обновить последний заказ"):
        st.rerun()
    response = api("GET", "/orders/latest", params={"customer_id": str(customer.id)})
    if response is None:
        st.info("У вас пока нет заказов")
        return
    order = OrderRes.model_validate(response)
    show_order(order)
    if not order.editable:
        st.info(
            "Заказ уже оформлен. Чтобы заказать другие товары, создайте новый заказ."
        )
        return

    with st.form(f"add_item_{order.id}", clear_on_submit=True):
        st.write("Добавить позицию")
        name = st.text_input("Название товара")
        quantity = st.number_input("Количество", min_value=1, step=1)
        price = st.number_input(
            "Цена за единицу, ₽", min_value=0.0, step=1.0, format="%.2f"
        )
        if st.form_submit_button("Добавить позицию"):
            save(
                "POST",
                f"/orders/{order.id}/items",
                OrderItemCreate(name=name, quantity=quantity, price=str(price)),
            )

    if order.items:
        items = {str(item.id): item for item in order.items}
        with st.form(f"remove_item_{order.id}"):
            item_id = st.selectbox(
                "Удалить позицию",
                list(items),
                format_func=lambda item_id: (
                    f"{items[item_id].name} × {items[item_id].quantity}"
                ),
            )
            if st.form_submit_button("Удалить позицию"):
                save("DELETE", f"/orders/{order.id}/items/{item_id}")

    with st.form(f"delivery_{order.id}"):
        delivery_type = st.radio(
            "Способ доставки", list(DELIVERY_LABELS), format_func=DELIVERY_LABELS.get
        )
        st.caption(
            "Выбор доставки подтверждает заказ. Курьер будет подобран автоматически."
        )
        if st.form_submit_button("Выбрать доставку и оформить заказ"):
            save(
                "PUT",
                f"/orders/{order.id}/delivery",
                DeliveryMethodUpdate(delivery_type=delivery_type),
            )


def admin_panel() -> None:
    st.caption(
        "Админские команды доступны всем; вкладка только визуально отделена от клиента."
    )
    couriers_tab, customers_tab, orders_tab = st.tabs(
        ["Курьеры", "Клиенты", "Заказы клиента"]
    )
    with couriers_tab:
        try:
            with st.form("create_courier", clear_on_submit=True):
                name = st.text_input("Имя курьера")
                phone = st.text_input("Телефон курьера")
                capacity = st.number_input(
                    "Вместимость, единиц товара", min_value=1, value=10, step=1
                )
                if st.form_submit_button("Добавить курьера"):
                    save(
                        "POST",
                        "/couriers",
                        CourierReq(name=name, phone=phone, capacity=capacity),
                    )
            if st.button("Обновить всех курьеров"):
                st.rerun()
            couriers = [
                CourierRes.model_validate(item) for item in api("GET", "/couriers")
            ]
            if couriers:
                st.dataframe(
                    [
                        {
                            "Имя": courier.name,
                            "Телефон": courier.phone,
                            "Вместимость": courier.capacity,
                            "Свободен": courier.available,
                        }
                        for courier in couriers
                    ],
                    hide_index=True,
                )
            else:
                st.info("Курьеров пока нет")
        except (RuntimeError, ValidationError) as error:
            st.error(str(error))

    with customers_tab:
        try:
            if st.button("Обновить всех клиентов"):
                st.rerun()
            customers = [
                CustomerRes.model_validate(item) for item in api("GET", "/customers")
            ]
            if customers:
                st.dataframe(
                    [item.model_dump(mode="json") for item in customers],
                    hide_index=True,
                )
            else:
                st.info("Клиентов пока нет")
        except (RuntimeError, ValidationError) as error:
            customers = []
            st.error(str(error))

    with orders_tab:
        try:
            if not customers:
                st.info("Сначала создайте клиента через вход")
                return
            options = {str(customer.id): customer for customer in customers}
            customer_id = st.selectbox(
                "Клиент",
                list(options),
                format_func=lambda customer_id: (
                    f"{options[customer_id].name}, {options[customer_id].phone}"
                ),
            )
            if st.button("Обновить все заказы клиента"):
                st.rerun()
            orders = [
                OrderRes.model_validate(item)
                for item in api("GET", "/orders", params={"customer_id": customer_id})
            ]
            if not orders:
                st.info("У этого клиента пока нет заказов")
            for order in orders:
                with st.expander(f"{order.created_at:%d.%m.%Y %H:%M} — {order.id}"):
                    show_order(order)
        except (RuntimeError, ValidationError) as error:
            st.error(str(error))


st.set_page_config(page_title="Служба доставки", layout="wide")
st.title("Служба доставки")
if notice := st.session_state.pop("notice", None):
    st.success(notice)
client_tab, admin_tab = st.tabs(["Клиент", "Админ"])
with client_tab:
    try:
        client_panel()
    except (RuntimeError, ValidationError) as error:
        st.error(str(error))
with admin_tab:
    admin_panel()
