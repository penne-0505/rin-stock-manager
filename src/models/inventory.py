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
    change: int  # + 入庫 / – 売上
    type: str  # 'sale' | 'restock'
    timestamp: datetime

    def __table_name__(cls) -> str:
        return "inventory_transactions"
