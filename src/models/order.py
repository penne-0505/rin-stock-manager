from datetime import datetime
from typing import List

from pydantic import BaseModel


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
    user_id: str

    def __table_name__(cls) -> str:
        return "orders"
