from uuid import UUID

from constants.options import FilterOp
from models.menu import MenuCategory, MenuItem
from repositories.bases.crud_repo import CrudRepository
from services.platform.client_service import SupabaseClient


# 仮インターフェース
class MenuItemRepository(CrudRepository[MenuItem, UUID]):
    """メニューアイテムリポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, MenuItem)

    async def find_by_category_id(
        self, category_id: UUID | None, user_id: UUID
    ) -> list[MenuItem]:
        """カテゴリIDでメニューアイテムを取得（None時は全件）"""

        filters = {"user_id": (FilterOp.EQ, user_id)}

        if category_id is not None:
            filters["category_id"] = (FilterOp.EQ, category_id)

        order_by = ("display_order", False)  # 表示順でソート

        return await self.find(filters=filters, order_by=order_by)

    async def find_available_only(self, user_id: UUID) -> list[MenuItem]:
        """販売可能なメニューアイテムのみ取得"""

        filters = {
            "user_id": (FilterOp.EQ, user_id),
            "is_available": (FilterOp.EQ, True),
        }

        order_by = ("display_order", False)  # 表示順でソート

        return await self.find(filters=filters, order_by=order_by)

    async def search_by_name(self, keyword: str, user_id: UUID) -> list[MenuItem]:
        """名前でメニューアイテムを検索"""

        if not keyword.strip():
            return []

        filters = {
            "user_id": (FilterOp.EQ, user_id),
            "name": (
                FilterOp.ILIKE,
                f"%{keyword.strip()}%",
            ),  # 大文字小文字を区別しないあいまい検索
        }

        order_by = ("display_order", False)  # 表示順でソート

        return await self.find(filters=filters, order_by=order_by)

    async def find_by_ids(
        self, menu_item_ids: list[UUID], user_id: UUID
    ) -> list[MenuItem]:
        """IDリストでメニューアイテムを取得"""

        if not menu_item_ids:
            return []

        filters = {
            "user_id": (FilterOp.EQ, user_id),
            "id": (FilterOp.IN, menu_item_ids),
        }

        return await self.find(filters=filters)


class MenuCategoryRepository(CrudRepository[MenuCategory, UUID]):
    """メニューカテゴリリポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, MenuCategory)

    async def find_active_ordered(self, user_id: UUID) -> list[MenuCategory]:
        """アクティブなカテゴリ一覧を表示順で取得"""

        filters = {"user_id": (FilterOp.EQ, user_id)}
        order_by = ("display_order", False)  # 昇順でソート

        return await self.find(filters=filters, order_by=order_by)
