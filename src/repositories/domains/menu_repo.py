from uuid import UUID


# 仮インターフェース
class IMenuItemRepository(ICRUDRepository[MenuItem], ABC):
    """メニューアイテムリポジトリ"""

    @abstractmethod
    async def find_by_category_id(
        self, category_id: Optional[UUID], user_id: UUID
    ) -> List[MenuItem]:
        """カテゴリIDでメニューアイテムを取得（None時は全件）"""
        pass

    @abstractmethod
    async def find_available_only(self, user_id: UUID) -> List[MenuItem]:
        """販売可能なメニューアイテムのみ取得"""
        pass

    @abstractmethod
    async def search_by_name(self, keyword: str, user_id: UUID) -> List[MenuItem]:
        """名前でメニューアイテムを検索"""
        pass

    @abstractmethod
    async def find_by_ids(
        self, menu_item_ids: List[UUID], user_id: UUID
    ) -> List[MenuItem]:
        """IDリストでメニューアイテムを取得"""
        pass


class IMenuCategoryRepository(ICRUDRepository[MenuCategory], ABC):
    """メニューカテゴリリポジトリ"""

    @abstractmethod
    async def find_active_ordered(self, user_id: UUID) -> List[MenuCategory]:
        """アクティブなカテゴリ一覧を表示順で取得"""
        pass
