from uuid import UUID
from datetime import datetime
from typing import Any

from models.order import Order, OrderItem
from constants.status import OrderStatus
from constants.types import Filter
from services.client_service import SupabaseClient
from src.repositories.abstract.crud_repo import CrudRepository

# 仮インターフェース
class OrderRepository(CrudRepository[Order, UUID]):
    """注文リポジトリ"""
    def __init__(self, client: SupabaseClient):
        super().__init__(client, Order)

    async def find_active_draft_by_user(self, user_id: UUID) -> Order | None:
        """ユーザーのアクティブな下書き注文（カート）を取得"""
        pass

    async def find_by_status_list(
        self, status_list: list[OrderStatus], user_id: UUID
    ) -> list[Order]:
        """指定ステータスリストの注文一覧を取得"""
        pass

    async def search_with_pagination(
        self, filter: Filter, page: int, limit: int
    ) -> tuple[list[Order], int]:
        """注文を検索（戻り値: (注文一覧, 総件数)）"""
        pass

    async def find_by_date_range(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> list[Order]:
        """期間指定で注文一覧を取得"""
        pass

    async def find_completed_by_date(
        self, target_date: datetime, user_id: UUID
    ) -> list[Order]:
        """指定日の完了注文を取得"""
        pass

    async def count_by_status_and_date(
        self, target_date: datetime, user_id: UUID
    ) -> dict[OrderStatus, int]:
        """指定日のステータス別注文数を取得"""
        pass

    async def generate_next_order_number(self, user_id: UUID) -> str:
        """次の注文番号を生成"""
        pass

    async def find_orders_by_completion_time_range(
        self, start_time: datetime, end_time: datetime, user_id: UUID
    ) -> list[Order]:
        """完了時間範囲で注文を取得（調理時間分析用）"""
        pass


class OrderItemRepository(CrudRepository[OrderItem, UUID]):
    """注文明細リポジトリ"""

    async def find_by_order_id(self, order_id: UUID) -> list[OrderItem]:
        """注文IDに紐づく明細一覧を取得"""
        pass

    async def find_existing_item(
        self, order_id: UUID, menu_item_id: UUID
    ) -> OrderItem | None:
        """注文内の既存アイテムを取得（重複チェック用）"""
        pass

    async def delete_by_order_id(self, order_id: UUID) -> bool:
        """注文IDに紐づく明細を全削除"""
        pass

    async def find_by_menu_item_and_date_range(
        self, menu_item_id: UUID, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> list[OrderItem]:
        """期間内の特定メニューアイテムの注文明細を取得"""
        pass

    async def get_menu_item_sales_summary(
        self, days: int, user_id: UUID
    ) -> list[dict[str, Any]]:
        """メニューアイテム別売上集計を取得"""
        pass
