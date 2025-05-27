from uuid import UUID

from models.inventory import InventoryItem, InventoryTransaction
from services.client_service import SupabaseClient
from src.repositories.abstract.crud_repo import CrudRepository


class InvItemRepository(CrudRepository[InventoryItem, UUID]):
    def __init__(self, client: SupabaseClient):
        super().__init__(client, InventoryItem)


class InvTxRepository(CrudRepository[InventoryTransaction, UUID]):
    def __init__(self, client: SupabaseClient):
        super().__init__(client, InventoryTransaction)


# 仮インターフェース
class IMaterialRepository(ICRUDRepository[Material], ABC):
    """材料リポジトリ"""

    @abstractmethod
    async def find_by_category_id(
        self, category_id: Optional[UUID], user_id: UUID
    ) -> List[Material]:
        """カテゴリIDで材料を取得（None時は全件）"""
        pass

    @abstractmethod
    async def find_below_alert_threshold(self, user_id: UUID) -> List[Material]:
        """アラート閾値を下回る材料を取得"""
        pass

    @abstractmethod
    async def find_below_critical_threshold(self, user_id: UUID) -> List[Material]:
        """緊急閾値を下回る材料を取得"""
        pass

    @abstractmethod
    async def find_by_ids(
        self, material_ids: List[UUID], user_id: UUID
    ) -> List[Material]:
        """IDリストで材料を取得"""
        pass

    @abstractmethod
    async def update_stock_amount(
        self, material_id: UUID, new_amount: Decimal, user_id: UUID
    ) -> Optional[Material]:
        """材料の在庫量を更新"""
        pass


class IMaterialCategoryRepository(ICRUDRepository[MaterialCategory], ABC):
    """材料カテゴリリポジトリ"""

    @abstractmethod
    async def find_active_ordered(self, user_id: UUID) -> List[MaterialCategory]:
        """アクティブなカテゴリ一覧を表示順で取得"""
        pass


class IRecipeRepository(ICRUDRepository[Recipe], ABC):
    """レシピリポジトリ"""

    @abstractmethod
    async def find_by_menu_item_id(
        self, menu_item_id: UUID, user_id: UUID
    ) -> List[Recipe]:
        """メニューアイテムIDでレシピ一覧を取得"""
        pass

    @abstractmethod
    async def find_by_material_id(
        self, material_id: UUID, user_id: UUID
    ) -> List[Recipe]:
        """材料IDを使用するレシピ一覧を取得"""
        pass

    @abstractmethod
    async def find_by_menu_item_ids(
        self, menu_item_ids: List[UUID], user_id: UUID
    ) -> List[Recipe]:
        """複数メニューアイテムのレシピを一括取得"""
        pass
