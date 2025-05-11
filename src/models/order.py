from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from constants.order_status import OrderStatus


class OrderItem(BaseModel):
    order_id: UUID
    inventory_item_id: UUID
    quantity: int

    def __table_name__(cls) -> str:
        return "order_items"


class Order(BaseModel):
    id: UUID | None = None
    items: list[OrderItem]
    total: Decimal
    timestamp: datetime
    status: OrderStatus
    user_id: UUID

    def __table_name__(cls) -> str:
        return "orders"
