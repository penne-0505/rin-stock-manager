from typing import Any
from uuid import UUID

from constants.transaction_mode import TransactionMode
from models.inventory import InventoryItem, InventoryTransaction


class InventoryService:
    def list_inventory(self) -> list[InventoryItem]:
        """全商品の在庫一覧を取得する"""

    def get_inventory_item(self, item_id: UUID) -> InventoryItem | None:
        """特定商品の在庫情報を取得する"""

    def update_stock(self, item_id: UUID, new_stock_amount: int) -> None:
        """在庫数を直接修正（棚卸しなど）"""

    def adjust_stock(
        self, item_id: UUID, change_amount: int, mode: TransactionMode
    ) -> InventoryTransaction:
        """在庫増減トランザクションを記録（仕入/売上/調整）"""

    def register_new_item(
        self,
        name: str,
        price: int,
        stock: int,
    ) -> InventoryItem:
        """新規商品を登録する"""

    def update_item_info(self, item_id: UUID, patch: dict[str, Any]) -> None:
        """商品の情報を更新する（名前・価格・カテゴリなど）"""
