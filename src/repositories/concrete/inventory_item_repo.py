from decimal import Decimal
from uuid import UUID

from models.inventory import InventoryItem
from repositories.abstruct.crud_repo import CrudRepository
from services.app_services.client_service import SupabaseClient


class InventoryItemRepository(CrudRepository[InventoryItem]):
    def __init__(self, client: SupabaseClient) -> None:
        super().__init__(client, InventoryItem.__table_name__(), InventoryItem)

    async def create_item(self, name: str, price: Decimal, stock: int) -> InventoryItem:
        """
        新しい在庫アイテムを作成します。

        Args:
            name (str): アイテムの名前。
            price (Decimal): アイテムの価格。
            stock (int): アイテムの在庫数。

        Returns:
            InventoryItem: 作成された在庫アイテム。
        """
        item = InventoryItem(name=name, price=price, stock=stock)
        return await self.create(item)

    async def get_all_items(self) -> list[InventoryItem]:
        """
        すべての在庫アイテムを取得します。

        Returns:
            list[InventoryItem]: 在庫アイテムのリスト。
        """
        return await self.list_entities()

    async def get_item_by_id(self, item_id: UUID) -> InventoryItem | None:
        """
        IDで在庫アイテムを取得します。

        Args:
            item_id (UUID): アイテムのID。

        Returns:
            InventoryItem | None: 在庫アイテム、または見つからない場合はNone。
        """
        return await self.read(str(item_id))

    async def upsert_item(
        self, item: InventoryItem, *, returning: bool = True
    ) -> InventoryItem | None:
        """
        在庫アイテムをアップサートします。

        Args:
            item (InventoryItem): アップサートする在庫アイテム。
            returning (bool): アップサート後のアイテムを返すかどうか。

        Returns:
            InventoryItem | None: アップサートされた在庫アイテム、またはNone。
        """
        return await self.upsert(item, returning=returning)

    async def delete_item(self, item_id: UUID) -> bool:
        """
        在庫アイテムを削除します。

        Args:
            item_id (UUID): 削除する在庫アイテムのID。

        Returns:
            bool: 削除が成功した場合はTrue、失敗した場合はFalse。
        """
        return await self.delete(str(item_id))
