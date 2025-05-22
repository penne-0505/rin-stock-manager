from datetime import datetime
from uuid import UUID

from constants.transaction_mode import TransactionMode
from models.base import CoreBaseModel


class InventoryItem(CoreBaseModel):
    id: UUID | None = None
    name: str
    price: int
    stock: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    alert_threshold: int | None = 50  # 在庫数がこの値を下回ったらアラート
    user_id: UUID | None = None

    def __table_name__(self) -> str:
        return "inventory_items"


class InventoryTransaction(CoreBaseModel):
    id: UUID | None = None
    item_id: UUID
    change: int  # 正の値は入庫、負の値は売上(出庫)。個数。
    type: TransactionMode
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    def __table_name__(self) -> str:
        return "inventory_transactions"
