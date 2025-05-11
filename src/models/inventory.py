from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from constants.transaction_mode import TransactionMode


class InventoryItem(BaseModel):
    id: UUID | None = None
    name: str
    price: Decimal
    stock: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    def __table_name__(cls) -> str:
        return "inventory_items"


class InventoryTransaction(BaseModel):
    id: UUID | None = None
    item_id: UUID
    change: int  # 正の値は入庫、負の値は売上(出庫)
    type: TransactionMode
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    def __table_name__(cls) -> str:
        return "inventory_transactions"
