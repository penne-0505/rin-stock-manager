from uuid import UUID

from models.inventory import MaterialUsageCalculation
from models.menu import MenuAvailabilityInfo, MenuCategory, MenuItem


class IMenuService:
    """メニュー管理サービス"""

    async def get_menu_categories(self, user_id: UUID) -> list[MenuCategory]:
        """メニューカテゴリ一覧を取得"""
        pass

    async def get_menu_items_by_category(
        self, category_id: UUID | None, user_id: UUID
    ) -> list[MenuItem]:
        """カテゴリ別メニューアイテム一覧を取得"""
        pass

    async def search_menu_items(self, keyword: str, user_id: UUID) -> list[MenuItem]:
        """メニューアイテムを検索"""
        pass

    async def check_menu_availability(
        self, menu_item_id: UUID, quantity: int, user_id: UUID
    ) -> MenuAvailabilityInfo:
        """メニューアイテムの在庫可否を詳細チェック"""
        pass

    async def get_unavailable_menu_items(self, user_id: UUID) -> list[UUID]:
        """在庫不足で販売不可なメニューアイテムIDを取得"""
        pass

    async def bulk_check_menu_availability(
        self, user_id: UUID
    ) -> dict[UUID, MenuAvailabilityInfo]:
        """全メニューアイテムの在庫可否を一括チェック"""
        pass

    async def calculate_max_servings(self, menu_item_id: UUID, user_id: UUID) -> int:
        """現在の在庫で作れる最大数を計算"""
        pass

    async def get_required_materials_for_menu(
        self, menu_item_id: UUID, quantity: int, user_id: UUID
    ) -> list[MaterialUsageCalculation]:
        """メニュー作成に必要な材料と使用量を計算"""
        pass

    async def toggle_menu_item_availability(
        self, menu_item_id: UUID, is_available: bool, user_id: UUID
    ) -> MenuItem:
        """メニューアイテムの販売可否を切り替え"""
        pass

    async def bulk_update_menu_availability(
        self, availability_updates: dict[UUID, bool], user_id: UUID
    ) -> dict[UUID, bool]:
        """メニューアイテムの販売可否を一括更新"""
        pass

    async def auto_update_menu_availability_by_stock(
        self, user_id: UUID
    ) -> dict[UUID, bool]:
        """在庫状況に基づいてメニューの販売可否を自動更新"""
        pass
