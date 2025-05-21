from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from models.base import CoreBaseModel


class Order(CoreBaseModel):
    id: UUID | None = None
    items: list[OrderItem]
    total: Decimal
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    def __table_name__(self) -> str:
        return "orders"


class OrderItem(CoreBaseModel):
    order_id: UUID
    inventory_item_id: UUID
    quantity: int

    def __table_name__(self) -> str:
        return "order_items"
