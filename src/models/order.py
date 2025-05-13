from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from constants.order_status import OrderStatus


class OrderItem(BaseModel):
    order_id: UUID
    inventory_item_id: UUID
    quantity: int

    def __table_name__() -> str:
        return "order_items"


class Order(BaseModel):
    id: UUID | None = None
    items: list[OrderItem]
    total: Decimal
    created_at: datetime | None = None
    updated_at: datetime | None = None
    queued_at: datetime | None = None
    completed_at: datetime | None = None
    status: OrderStatus
    user_id: UUID | None = None

    def __table_name__() -> str:
        return "orders"
