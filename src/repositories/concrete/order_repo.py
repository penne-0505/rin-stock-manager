from uuid import UUID

from models.order import Order, OrderItem
from services.client_service import SupabaseClient
from src.repositories.abstract.crud_repo import CrudRepository


class OrderRepository(CrudRepository[Order, UUID]):
    def __init__(self, client: SupabaseClient):
        super().__init__(client, Order)


class OrderItemRepository(CrudRepository[OrderItem, UUID]):
    def __init__(self, client: SupabaseClient):
        super().__init__(client, OrderItem)


# 仮インターフェース
class IOrderRepository(ICRUDRepository[Order], ABC):
    """注文リポジトリ"""

    @abstractmethod
    async def find_active_draft_by_user(self, user_id: UUID) -> Optional[Order]:
        """ユーザーのアクティブな下書き注文（カート）を取得"""
        pass

    @abstractmethod
    async def find_by_status_list(
        self, status_list: List[OrderStatus], user_id: UUID
    ) -> List[Order]:
        """指定ステータスリストの注文一覧を取得"""
        pass

    @abstractmethod
    async def search_with_pagination(
        self, filters: Filters, page: int, limit: int
    ) -> Tuple[List[Order], int]:
        """注文を検索（戻り値: (注文一覧, 総件数)）"""
        pass

    @abstractmethod
    async def find_by_date_range(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> List[Order]:
        """期間指定で注文一覧を取得"""
        pass

    @abstractmethod
    async def find_completed_by_date(
        self, target_date: datetime, user_id: UUID
    ) -> List[Order]:
        """指定日の完了注文を取得"""
        pass

    @abstractmethod
    async def count_by_status_and_date(
        self, target_date: datetime, user_id: UUID
    ) -> Dict[OrderStatus, int]:
        """指定日のステータス別注文数を取得"""
        pass

    @abstractmethod
    async def generate_next_order_number(self, user_id: UUID) -> str:
        """次の注文番号を生成"""
        pass

    @abstractmethod
    async def find_orders_by_completion_time_range(
        self, start_time: datetime, end_time: datetime, user_id: UUID
    ) -> List[Order]:
        """完了時間範囲で注文を取得（調理時間分析用）"""
        pass


class IOrderItemRepository(ICRUDRepository[OrderItem], ABC):
    """注文明細リポジトリ"""

    @abstractmethod
    async def find_by_order_id(self, order_id: UUID) -> List[OrderItem]:
        """注文IDに紐づく明細一覧を取得"""
        pass

    @abstractmethod
    async def find_existing_item(
        self, order_id: UUID, menu_item_id: UUID
    ) -> Optional[OrderItem]:
        """注文内の既存アイテムを取得（重複チェック用）"""
        pass

    @abstractmethod
    async def delete_by_order_id(self, order_id: UUID) -> bool:
        """注文IDに紐づく明細を全削除"""
        pass

    @abstractmethod
    async def find_by_menu_item_and_date_range(
        self, menu_item_id: UUID, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> List[OrderItem]:
        """期間内の特定メニューアイテムの注文明細を取得"""
        pass

    @abstractmethod
    async def get_menu_item_sales_summary(
        self, days: int, user_id: UUID
    ) -> List[Dict[str, Any]]:
        """メニューアイテム別売上集計を取得"""
        pass
