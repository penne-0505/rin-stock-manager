class IMenuService(ABC):
    """メニュー管理サービス"""

    @abstractmethod
    async def get_menu_categories(self, user_id: UUID) -> List[MenuCategory]:
        """メニューカテゴリ一覧を取得"""
        pass

    @abstractmethod
    async def get_menu_items_by_category(
        self, category_id: Optional[UUID], user_id: UUID
    ) -> List[MenuItem]:
        """カテゴリ別メニューアイテム一覧を取得"""
        pass

    @abstractmethod
    async def search_menu_items(self, keyword: str, user_id: UUID) -> List[MenuItem]:
        """メニューアイテムを検索"""
        pass

    @abstractmethod
    async def check_menu_availability(
        self, menu_item_id: UUID, quantity: int, user_id: UUID
    ) -> MenuAvailabilityInfo:
        """メニューアイテムの在庫可否を詳細チェック"""
        pass

    @abstractmethod
    async def get_unavailable_menu_items(self, user_id: UUID) -> List[UUID]:
        """在庫不足で販売不可なメニューアイテムIDを取得"""
        pass

    @abstractmethod
    async def bulk_check_menu_availability(
        self, user_id: UUID
    ) -> Dict[UUID, MenuAvailabilityInfo]:
        """全メニューアイテムの在庫可否を一括チェック"""
        pass

    @abstractmethod
    async def calculate_max_servings(self, menu_item_id: UUID, user_id: UUID) -> int:
        """現在の在庫で作れる最大数を計算"""
        pass

    @abstractmethod
    async def get_required_materials_for_menu(
        self, menu_item_id: UUID, quantity: int, user_id: UUID
    ) -> List[MaterialUsageCalculation]:
        """メニュー作成に必要な材料と使用量を計算"""
        pass

    @abstractmethod
    async def toggle_menu_item_availability(
        self, menu_item_id: UUID, is_available: bool, user_id: UUID
    ) -> MenuItem:
        """メニューアイテムの販売可否を切り替え"""
        pass

    @abstractmethod
    async def bulk_update_menu_availability(
        self, availability_updates: Dict[UUID, bool], user_id: UUID
    ) -> Dict[UUID, bool]:
        """メニューアイテムの販売可否を一括更新"""
        pass

    @abstractmethod
    async def auto_update_menu_availability_by_stock(
        self, user_id: UUID
    ) -> Dict[UUID, bool]:
        """在庫状況に基づいてメニューの販売可否を自動更新"""
        pass
