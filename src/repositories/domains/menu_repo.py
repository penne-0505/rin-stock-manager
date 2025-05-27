from uuid import UUID

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
        pass

    async def find_available_only(self, user_id: UUID) -> list[MenuItem]:
        """販売可能なメニューアイテムのみ取得"""
        pass

    async def search_by_name(self, keyword: str, user_id: UUID) -> list[MenuItem]:
        """名前でメニューアイテムを検索"""
        pass

    async def find_by_ids(
        self, menu_item_ids: list[UUID], user_id: UUID
    ) -> list[MenuItem]:
        """IDリストでメニューアイテムを取得"""
        pass


class MenuCategoryRepository(CrudRepository[MenuCategory, UUID]):
    """メニューカテゴリリポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, MenuCategory)

    async def find_active_ordered(self, user_id: UUID) -> list[MenuCategory]:
        """アクティブなカテゴリ一覧を表示順で取得"""
        pass
