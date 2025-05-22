from __future__ import annotations

from datetime import datetime
from uuid import UUID

from constants.order_status import OrderStatus
from models.base import CoreBaseModel


class Order(CoreBaseModel):
    id: UUID | None = None
    items: list[OrderItem]
    total: int
    status: OrderStatus
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None
    # 割引率である場合は、ロジック側で計算する
    discount_amount: int | None = 0
    payment_method: str | None = None

    def __table_name__(self) -> str:
        return "orders"


class OrderItem(CoreBaseModel):
    order_id: UUID
    inventory_item_id: UUID
    price_at_order: int
    options: dict[str, str | bool] | None = None  # 「ソース: あり/なし」みたいなこと
    quantity: int

    def __table_name__(self) -> str:
        return "order_items"
