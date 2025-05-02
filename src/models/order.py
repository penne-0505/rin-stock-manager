from datetime import datetime
from typing import List

from pydantic import BaseModel


class OrderItem(BaseModel):
    inventory_item_id: str
    quantity: int


class Order(BaseModel):
    id: str
    items: List[OrderItem]
    total: float
    timestamp: datetime
