from services.platform.client_service import SupabaseClient
from uuid import UUID
from models.stock import Purchase, PurchaseItem, StockAdjustment, StockTransaction
from datetime import datetime
from repositories.bases.crud_repo import CrudRepository

# 仮インターフェース
class PurchaseRepository(CrudRepository[Purchase, UUID]):
    """仕入れリポジトリ"""
    def __init__(self, client: SupabaseClient):
        super().__init__(client, Purchase)

    async def find_recent(self, days: int, user_id: UUID) -> list[Purchase]:
        """最近の仕入れ一覧を取得"""
        pass

    async def find_by_date_range(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> list[Purchase]:
        """期間指定で仕入れ一覧を取得"""
        pass


class IPurchaseItemRepository(CrudRepository[PurchaseItem, UUID]):
    """仕入れ明細リポジトリ"""
    def __init__(self, client: SupabaseClient):
        super().__init__(client, PurchaseItem)

    async def find_by_purchase_id(self, purchase_id: UUID) -> list[PurchaseItem]:
        """仕入れIDで明細一覧を取得"""
        pass

    async def create_batch(
        self, purchase_items: list[PurchaseItem]
    ) -> list[PurchaseItem]:
        """仕入れ明細を一括作成"""
        pass


class IStockAdjustmentRepository(CrudRepository[StockAdjustment, UUID]):
    """在庫調整リポジトリ"""
    def __init__(self, client: SupabaseClient):
        super().__init__(client, StockAdjustment)

    async def find_by_material_id(
        self, material_id: UUID, user_id: UUID
    ) -> list[StockAdjustment]:
        """材料IDで調整履歴を取得"""
        pass

    async def find_recent(self, days: int, user_id: UUID) -> list[StockAdjustment]:
        """最近の調整履歴を取得"""
        pass


class IStockTransactionRepository(CrudRepository[StockTransaction, UUID]):
    """在庫取引リポジトリ"""
    def __init__(self, client: SupabaseClient):
        super().__init__(client, StockTransaction)

    async def create_batch(
        self, transactions: list[StockTransaction]
    ) -> list[StockTransaction]:
        """在庫取引を一括作成"""
        pass

    async def find_by_reference(
        self, reference_type: str, reference_id: UUID, user_id: UUID
    ) -> list[StockTransaction]:
        """参照タイプ・IDで取引履歴を取得"""
        pass

    async def find_by_material_and_date_range(
        self, material_id: UUID, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> list[StockTransaction]:
        """材料IDと期間で取引履歴を取得"""
        pass

    async def find_consumption_transactions(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> list[StockTransaction]:
        """期間内の消費取引（負の値）を取得"""
        pass
