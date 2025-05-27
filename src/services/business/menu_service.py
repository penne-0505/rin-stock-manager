from uuid import UUID

from constants.options import FilterOp
from models.inventory import MaterialUsageCalculation
from models.menu import MenuAvailabilityInfo, MenuCategory, MenuItem
from repositories.domains.inventory_repo import MaterialRepository, RecipeRepository
from repositories.domains.menu_repo import MenuCategoryRepository, MenuItemRepository
from services.platform.client_service import SupabaseClient


class MenuService:
    """メニュー管理サービス"""

    def __init__(self, client: SupabaseClient):
        self.menu_item_repo = MenuItemRepository(client)
        self.menu_category_repo = MenuCategoryRepository(client)
        self.material_repo = MaterialRepository(client)
        self.recipe_repo = RecipeRepository(client)

    async def get_menu_categories(self, user_id: UUID) -> list[MenuCategory]:
        """メニューカテゴリ一覧を取得"""
        filters = {"user_id": (FilterOp.EQ, user_id)}
        order_by = ("display_order", False)
        return await self.menu_category_repo.find(filters=filters, order_by=order_by)

    async def get_menu_items_by_category(
        self, category_id: UUID | None, user_id: UUID
    ) -> list[MenuItem]:
        """カテゴリ別メニューアイテム一覧を取得"""
        filters = {"user_id": (FilterOp.EQ, user_id)}
        if category_id is not None:
            filters["category_id"] = (FilterOp.EQ, category_id)

        order_by = ("display_order", False)
        return await self.menu_item_repo.find(filters=filters, order_by=order_by)

    async def search_menu_items(self, keyword: str, user_id: UUID) -> list[MenuItem]:
        """メニューアイテムを検索"""
        # ユーザーでフィルタリング
        user_filter = {"user_id": (FilterOp.EQ, user_id)}

        # まずユーザーでフィルタリングしてから検索
        user_items = await self.menu_item_repo.find(filters=user_filter)

        # 手動でキーワード検索（Supabaseの制限回避）
        matching_items = []
        for item in user_items:
            if keyword.lower() in item.name.lower() or (
                item.description and keyword.lower() in item.description.lower()
            ):
                matching_items.append(item)

        return matching_items

    async def check_menu_availability(
        self, menu_item_id: UUID, quantity: int, user_id: UUID
    ) -> MenuAvailabilityInfo:
        """メニューアイテムの在庫可否を詳細チェック"""
        # メニューアイテムを取得
        menu_item = await self.menu_item_repo.find_by_id(menu_item_id)
        if not menu_item or menu_item.user_id != user_id:
            return MenuAvailabilityInfo(
                menu_item_id=menu_item_id,
                is_available=False,
                missing_materials=["Menu item not found"],
                estimated_servings=0,
            )

        # メニューアイテムが無効になっている場合
        if not menu_item.is_available:
            return MenuAvailabilityInfo(
                menu_item_id=menu_item_id,
                is_available=False,
                missing_materials=["Menu item disabled"],
                estimated_servings=0,
            )

        # レシピを取得
        recipe_filters = {
            "menu_item_id": (FilterOp.EQ, menu_item_id),
            "user_id": (FilterOp.EQ, user_id),
        }
        recipes = await self.recipe_repo.find(filters=recipe_filters)

        if not recipes:
            # レシピがない場合は作成可能とみなす
            return MenuAvailabilityInfo(
                menu_item_id=menu_item_id,
                is_available=True,
                missing_materials=[],
                estimated_servings=quantity,
            )

        missing_materials = []
        max_servings = float("inf")

        for recipe in recipes:
            # 材料を取得
            material = await self.material_repo.find_by_id(recipe.material_id)
            if not material or material.user_id != user_id:
                continue

            required_amount = recipe.required_amount * quantity
            available_amount = material.current_stock

            if not recipe.is_optional and available_amount < required_amount:
                missing_materials.append(material.name)

            # 最大作成可能数を計算
            if not recipe.is_optional and recipe.required_amount > 0:
                possible_servings = int(available_amount / recipe.required_amount)
                max_servings = min(max_servings, possible_servings)

        if max_servings == float("inf"):
            max_servings = quantity

        is_available = len(missing_materials) == 0 and max_servings >= quantity

        return MenuAvailabilityInfo(
            menu_item_id=menu_item_id,
            is_available=is_available,
            missing_materials=missing_materials,
            estimated_servings=max_servings,
        )

    async def get_unavailable_menu_items(self, user_id: UUID) -> list[UUID]:
        """在庫不足で販売不可なメニューアイテムIDを取得"""
        # 全メニューアイテムを取得
        menu_filters = {"user_id": (FilterOp.EQ, user_id)}
        menu_items = await self.menu_item_repo.find(filters=menu_filters)

        unavailable_items = []

        for menu_item in menu_items:
            if not menu_item.is_available:
                unavailable_items.append(menu_item.id)
                continue

            # 在庫チェック
            availability = await self.check_menu_availability(menu_item.id, 1, user_id)
            if not availability.is_available:
                unavailable_items.append(menu_item.id)

        return unavailable_items

    async def bulk_check_menu_availability(
        self, user_id: UUID
    ) -> dict[UUID, MenuAvailabilityInfo]:
        """全メニューアイテムの在庫可否を一括チェック"""
        # 全メニューアイテムを取得
        menu_filters = {"user_id": (FilterOp.EQ, user_id)}
        menu_items = await self.menu_item_repo.find(filters=menu_filters)

        availability_info = {}

        for menu_item in menu_items:
            availability = await self.check_menu_availability(menu_item.id, 1, user_id)
            availability_info[menu_item.id] = availability

        return availability_info

    async def calculate_max_servings(self, menu_item_id: UUID, user_id: UUID) -> int:
        """現在の在庫で作れる最大数を計算"""
        # レシピを取得
        recipe_filters = {
            "menu_item_id": (FilterOp.EQ, menu_item_id),
            "user_id": (FilterOp.EQ, user_id),
        }
        recipes = await self.recipe_repo.find(filters=recipe_filters)

        if not recipes:
            # レシピがない場合は無制限とみなす（実際には業務ルールに依存）
            return 999999

        max_servings = float("inf")

        for recipe in recipes:
            if recipe.is_optional:
                continue

            # 材料を取得
            material = await self.material_repo.find_by_id(recipe.material_id)
            if not material or material.user_id != user_id:
                continue

            if recipe.required_amount > 0:
                possible_servings = int(material.current_stock / recipe.required_amount)
                max_servings = min(max_servings, possible_servings)

        return int(max_servings) if max_servings != float("inf") else 0

    async def get_required_materials_for_menu(
        self, menu_item_id: UUID, quantity: int, user_id: UUID
    ) -> list[MaterialUsageCalculation]:
        """メニュー作成に必要な材料と使用量を計算"""
        # レシピを取得
        recipe_filters = {
            "menu_item_id": (FilterOp.EQ, menu_item_id),
            "user_id": (FilterOp.EQ, user_id),
        }
        recipes = await self.recipe_repo.find(filters=recipe_filters)

        calculations = []

        for recipe in recipes:
            # 材料を取得
            material = await self.material_repo.find_by_id(recipe.material_id)
            if not material or material.user_id != user_id:
                continue

            required_amount = recipe.required_amount * quantity
            available_amount = material.current_stock
            is_sufficient = available_amount >= required_amount

            calculation = MaterialUsageCalculation(
                material_id=recipe.material_id,
                required_amount=required_amount,
                available_amount=available_amount,
                is_sufficient=is_sufficient,
            )
            calculations.append(calculation)

        return calculations

    async def toggle_menu_item_availability(
        self, menu_item_id: UUID, is_available: bool, user_id: UUID
    ) -> MenuItem:
        """メニューアイテムの販売可否を切り替え"""
        # メニューアイテムを取得
        menu_item = await self.menu_item_repo.find_by_id(menu_item_id)
        if not menu_item or menu_item.user_id != user_id:
            raise ValueError(f"Menu item not found or access denied: {menu_item_id}")

        # 可否状態を更新
        menu_item.is_available = is_available

        # 更新
        updated_item = await self.menu_item_repo.update(menu_item_id, menu_item)
        return updated_item

    async def bulk_update_menu_availability(
        self, availability_updates: dict[UUID, bool], user_id: UUID
    ) -> dict[UUID, bool]:
        """メニューアイテムの販売可否を一括更新"""
        results = {}

        for menu_item_id, is_available in availability_updates.items():
            try:
                await self.toggle_menu_item_availability(
                    menu_item_id, is_available, user_id
                )
                results[menu_item_id] = is_available
            except ValueError:
                # アクセス権限がない場合はスキップ
                results[menu_item_id] = False

        return results

    async def auto_update_menu_availability_by_stock(
        self, user_id: UUID
    ) -> dict[UUID, bool]:
        """在庫状況に基づいてメニューの販売可否を自動更新"""
        # 全メニューアイテムの在庫状況をチェック
        availability_info = await self.bulk_check_menu_availability(user_id)

        updates = {}
        results = {}

        for menu_item_id, info in availability_info.items():
            # 在庫に基づく可否状態を決定
            should_be_available = info.is_available and info.estimated_servings > 0

            # 現在のメニューアイテムを取得して状態比較
            menu_item = await self.menu_item_repo.find_by_id(menu_item_id)
            if menu_item and menu_item.is_available != should_be_available:
                updates[menu_item_id] = should_be_available

        # 一括更新
        if updates:
            results = await self.bulk_update_menu_availability(updates, user_id)

        return results
