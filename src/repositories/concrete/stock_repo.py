from datetime import datetime


# 仮インターフェース
class IPurchaseRepository(ICRUDRepository[Purchase], ABC):
    """仕入れリポジトリ"""

    @abstractmethod
    async def find_recent(self, days: int, user_id: UUID) -> List[Purchase]:
        """最近の仕入れ一覧を取得"""
        pass

    @abstractmethod
    async def find_by_date_range(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> List[Purchase]:
        """期間指定で仕入れ一覧を取得"""
        pass


class IPurchaseItemRepository(ICRUDRepository[PurchaseItem], ABC):
    """仕入れ明細リポジトリ"""

    @abstractmethod
    async def find_by_purchase_id(self, purchase_id: UUID) -> List[PurchaseItem]:
        """仕入れIDで明細一覧を取得"""
        pass

    @abstractmethod
    async def create_batch(
        self, purchase_items: List[PurchaseItem]
    ) -> List[PurchaseItem]:
        """仕入れ明細を一括作成"""
        pass


class IStockAdjustmentRepository(ICRUDRepository[StockAdjustment], ABC):
    """在庫調整リポジトリ"""

    @abstractmethod
    async def find_by_material_id(
        self, material_id: UUID, user_id: UUID
    ) -> List[StockAdjustment]:
        """材料IDで調整履歴を取得"""
        pass

    @abstractmethod
    async def find_recent(self, days: int, user_id: UUID) -> List[StockAdjustment]:
        """最近の調整履歴を取得"""
        pass


class IStockTransactionRepository(ICRUDRepository[StockTransaction], ABC):
    """在庫取引リポジトリ"""

    @abstractmethod
    async def create_batch(
        self, transactions: List[StockTransaction]
    ) -> List[StockTransaction]:
        """在庫取引を一括作成"""
        pass

    @abstractmethod
    async def find_by_reference(
        self, reference_type: str, reference_id: UUID, user_id: UUID
    ) -> List[StockTransaction]:
        """参照タイプ・IDで取引履歴を取得"""
        pass

    @abstractmethod
    async def find_by_material_and_date_range(
        self, material_id: UUID, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> List[StockTransaction]:
        """材料IDと期間で取引履歴を取得"""
        pass

    @abstractmethod
    async def find_consumption_transactions(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> List[StockTransaction]:
        """期間内の消費取引（負の値）を取得"""
        pass
