from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from constants.transaction_mode import TransactionMode


class InventoryItem(BaseModel):
    id: UUID | None = None
    name: str
    price: Decimal

    def __table_name__(cls) -> str:
        return "inventory_items"


class InventoryTransaction(BaseModel):
    id: UUID | None = None
    item_id: UUID
    change: int  # 正の値は入庫、負の値は売上(出庫)
    type: TransactionMode
    timestamp: datetime
    user_id: UUID

    def __table_name__(cls) -> str:
        return "inventory_transactions"
