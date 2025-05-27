from decimal import Decimal
from uuid import UUID

from constants.options import FilterOp
from models.inventory import Material, MaterialCategory, Recipe
from repositories.bases.crud_repo import CrudRepository
from services.platform.client_service import SupabaseClient


# 仮インターフェース
class MaterialRepository(CrudRepository[Material, UUID]):
    """材料リポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, Material)

    async def find_by_category_id(
        self, category_id: UUID | None, user_id: UUID
    ) -> list[Material]:
        """カテゴリIDで材料を取得（None時は全件）"""

        filters = {"user_id": (FilterOp.EQ, user_id)}

        if category_id is not None:
            filters["category_id"] = (FilterOp.EQ, category_id)

        return await self.find(filters=filters)

    async def find_below_alert_threshold(self, user_id: UUID) -> list[Material]:
        """アラート閾値を下回る材料を取得"""

        # ユーザーIDでフィルタして全材料を取得
        filters = {"user_id": (FilterOp.EQ, user_id)}
        all_materials = await self.find(filters=filters)

        # アラート閾値以下の材料をフィルタ
        return [
            material
            for material in all_materials
            if material.current_stock <= material.alert_threshold
        ]

    async def find_below_critical_threshold(self, user_id: UUID) -> list[Material]:
        """緊急閾値を下回る材料を取得"""

        # ユーザーIDでフィルタして全材料を取得
        filters = {"user_id": (FilterOp.EQ, user_id)}
        all_materials = await self.find(filters=filters)

        # 緊急閾値以下の材料をフィルタ
        return [
            material
            for material in all_materials
            if material.current_stock <= material.critical_threshold
        ]

    async def find_by_ids(
        self, material_ids: list[UUID], user_id: UUID
    ) -> list[Material]:
        """IDリストで材料を取得"""

        if not material_ids:
            return []

        filters = {"user_id": (FilterOp.EQ, user_id), "id": (FilterOp.IN, material_ids)}

        return await self.find(filters=filters)

    async def update_stock_amount(
        self, material_id: UUID, new_amount: Decimal, user_id: UUID
    ) -> Material | None:
        """材料の在庫量を更新"""

        # 対象材料を取得
        filters = {"id": (FilterOp.EQ, material_id), "user_id": (FilterOp.EQ, user_id)}

        materials = await self.find(filters=filters, limit=1)
        if not materials:
            return None

        material = materials[0]

        # 在庫量を更新
        update_data = {"current_stock": new_amount}
        updated_material = await self.update(material_id, update_data)

        return updated_material


class MaterialCategoryRepository(CrudRepository[MaterialCategory, UUID]):
    """材料カテゴリリポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, MaterialCategory)

    async def find_active_ordered(self, user_id: UUID) -> list[MaterialCategory]:
        """アクティブなカテゴリ一覧を表示順で取得"""

        filters = {"user_id": (FilterOp.EQ, user_id)}
        order_by = ("display_order", False)  # 昇順でソート

        return await self.find(filters=filters, order_by=order_by)


class RecipeRepository(CrudRepository[Recipe, UUID]):
    """レシピリポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, Recipe)

    async def find_by_menu_item_id(
        self, menu_item_id: UUID, user_id: UUID
    ) -> list[Recipe]:
        """メニューアイテムIDでレシピ一覧を取得"""

        filters = {
            "menu_item_id": (FilterOp.EQ, menu_item_id),
            "user_id": (FilterOp.EQ, user_id),
        }

        return await self.find(filters=filters)

    async def find_by_material_id(
        self, material_id: UUID, user_id: UUID
    ) -> list[Recipe]:
        """材料IDを使用するレシピ一覧を取得"""

        filters = {
            "material_id": (FilterOp.EQ, material_id),
            "user_id": (FilterOp.EQ, user_id),
        }

        return await self.find(filters=filters)

    async def find_by_menu_item_ids(
        self, menu_item_ids: list[UUID], user_id: UUID
    ) -> list[Recipe]:
        """複数メニューアイテムのレシピを一括取得"""

        if not menu_item_ids:
            return []

        filters = {
            "menu_item_id": (FilterOp.IN, menu_item_ids),
            "user_id": (FilterOp.EQ, user_id),
        }

        return await self.find(filters=filters)
