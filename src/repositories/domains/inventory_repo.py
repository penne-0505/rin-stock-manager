from uuid import UUID
from models.inventory import Material, MaterialCategory, Recipe
from decimal import Decimal

from services.platform.client_service import SupabaseClient
from repositories.bases.crud_repo import CrudRepository


# 仮インターフェース
class MaterialRepository(CrudRepository[Material, UUID]):
    """材料リポジトリ"""
    def __init__(self, client: SupabaseClient):
        super().__init__(client, Material)

    async def find_by_category_id(
        self, category_id: UUID | None, user_id: UUID
    ) -> list[Material]:
        """カテゴリIDで材料を取得（None時は全件）"""
        pass

    async def find_below_alert_threshold(self, user_id: UUID) -> list[Material]:
        """アラート閾値を下回る材料を取得"""
        pass

    async def find_below_critical_threshold(self, user_id: UUID) -> list[Material]:
        """緊急閾値を下回る材料を取得"""
        pass

    async def find_by_ids(
        self, material_ids: list[UUID], user_id: UUID
    ) -> list[Material]:
        """IDリストで材料を取得"""
        pass

    async def update_stock_amount(
        self, material_id: UUID, new_amount: Decimal, user_id: UUID
    ) -> Material | None:
        """材料の在庫量を更新"""
        pass


class MaterialCategoryRepository(CrudRepository[MaterialCategory, UUID]):
    """材料カテゴリリポジトリ"""
    def __init__(self, client: SupabaseClient):
        super().__init__(client, MaterialCategory)

    async def find_active_ordered(self, user_id: UUID) -> list[MaterialCategory]:
        """アクティブなカテゴリ一覧を表示順で取得"""
        pass


class RecipeRepository(CrudRepository[Recipe, UUID]):
    """レシピリポジトリ"""
    def __init__(self, client: SupabaseClient):
        super().__init__(client, Recipe)

    async def find_by_menu_item_id(
        self, menu_item_id: UUID, user_id: UUID
    ) -> list[Recipe]:
        """メニューアイテムIDでレシピ一覧を取得"""
        pass

    async def find_by_material_id(
        self, material_id: UUID, user_id: UUID
    ) -> list[Recipe]:
        """材料IDを使用するレシピ一覧を取得"""
        pass

    async def find_by_menu_item_ids(
        self, menu_item_ids: list[UUID], user_id: UUID
    ) -> list[Recipe]:
        """複数メニューアイテムのレシピを一括取得"""
        pass
