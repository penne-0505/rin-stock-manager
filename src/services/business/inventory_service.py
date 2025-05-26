from uuid import UUID


class IInventoryService(ABC):
    """在庫管理サービス"""

    @abstractmethod
    async def get_material_categories(self, user_id: UUID) -> List[MaterialCategory]:
        """材料カテゴリ一覧を取得"""
        pass

    @abstractmethod
    async def get_materials_by_category(
        self, category_id: Optional[UUID], user_id: UUID
    ) -> List[Material]:
        """カテゴリ別材料一覧を取得"""
        pass

    @abstractmethod
    async def get_stock_alerts_by_level(
        self, user_id: UUID
    ) -> Dict[StockLevel, List[Material]]:
        """在庫レベル別アラート材料を取得"""
        pass

    @abstractmethod
    async def get_critical_stock_materials(self, user_id: UUID) -> List[Material]:
        """緊急レベルの材料一覧を取得"""
        pass

    @abstractmethod
    async def update_material_stock(
        self, request: StockUpdateRequest, user_id: UUID
    ) -> Material:
        """材料在庫を手動更新"""
        pass

    @abstractmethod
    async def record_purchase(self, request: PurchaseRequest, user_id: UUID) -> UUID:
        """仕入れを記録し、在庫を増加"""
        pass

    @abstractmethod
    async def get_materials_with_stock_info(
        self, category_id: Optional[UUID], user_id: UUID
    ) -> List[MaterialStockInfo]:
        """材料一覧を在庫レベル・使用可能日数付きで取得"""
        pass

    @abstractmethod
    async def calculate_material_usage_rate(
        self, material_id: UUID, days: int, user_id: UUID
    ) -> Optional[Decimal]:
        """材料の平均使用量を計算（日次）"""
        pass

    @abstractmethod
    async def calculate_estimated_usage_days(
        self, material_id: UUID, user_id: UUID
    ) -> Optional[int]:
        """推定使用可能日数を計算"""
        pass

    @abstractmethod
    async def bulk_calculate_usage_days(
        self, user_id: UUID
    ) -> Dict[UUID, Optional[int]]:
        """全材料の使用可能日数を一括計算"""
        pass

    @abstractmethod
    async def get_detailed_stock_alerts(
        self, user_id: UUID
    ) -> Dict[str, List[MaterialStockInfo]]:
        """詳細な在庫アラート情報を取得（レベル別 + 詳細情報付き）"""
        pass

    @abstractmethod
    async def consume_materials_for_order(self, order_id: UUID, user_id: UUID) -> bool:
        """注文に対する材料を消費（在庫減算）"""
        pass

    @abstractmethod
    async def restore_materials_for_order(self, order_id: UUID, user_id: UUID) -> bool:
        """注文キャンセル時の材料を復元（在庫復旧）"""
        pass

    @abstractmethod
    async def update_material_thresholds(
        self,
        material_id: UUID,
        alert_threshold: Decimal,
        critical_threshold: Decimal,
        user_id: UUID,
    ) -> Material:
        """材料のアラート閾値を更新"""
        pass
