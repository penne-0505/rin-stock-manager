from datetime import datetime

from pydantic import BaseModel


class InventoryItem(BaseModel):
    id: str
    name: str
    price: float

    def __table_name__(cls) -> str:
        return "inventory_items"


class InventoryTransaction(BaseModel):
    id: str
    item_id: str
    change: int
    type: str
    timestamp: datetime
    user_id: str

    def __table_name__(cls) -> str:
        return "inventory_transactions"
