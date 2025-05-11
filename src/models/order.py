from datetime import datetime
from typing import List

from pydantic import BaseModel

from constants.order_status import OrderStatus


class OrderItem(BaseModel):
    inventory_item_id: str
    quantity: int

    def __table_name__(cls) -> str:
        return "order_items"


class Order(BaseModel):
    id: str
    items: List[OrderItem]
    total: float
    timestamp: datetime
    status: OrderStatus
    user_id: str

    def __table_name__(cls) -> str:
        return "orders"
