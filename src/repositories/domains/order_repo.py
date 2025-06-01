from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from constants.options import FilterOp
from constants.status import OrderStatus
from constants.types import Filter
from models.domains.order import Order, OrderItem
from repositories.bases.crud_repo import CrudRepository
from services.platform.client_service import SupabaseClient


# 仮インターフェース
class OrderRepository(CrudRepository[Order, UUID]):
    """注文リポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, Order)

    async def find_active_draft_by_user(self, user_id: UUID) -> Order | None:
        """ユーザーのアクティブな下書き注文（カート）を取得"""
        filters = {
            "user_id": (FilterOp.EQ, user_id),
            "status": (FilterOp.EQ, OrderStatus.PREPARING),
        }

        # 最新のものを取得
        order_by = ("created_at", True)  # 作成日時で降順

        results = await self.find(filters=filters, order_by=order_by, limit=1)
        return results[0] if results else None

    async def find_by_status_list(
        self, status_list: list[OrderStatus], user_id: UUID
    ) -> list[Order]:
        """指定ステータスリストの注文一覧を取得"""
        if not status_list:
            return []

        filters = {
            "user_id": (FilterOp.EQ, user_id),
            "status": (FilterOp.IN, status_list),
        }

        # 注文日時で降順
        order_by = ("ordered_at", True)

        return await self.find(filters=filters, order_by=order_by)

    async def search_with_pagination(
        self, filter: Filter, page: int, limit: int
    ) -> tuple[list[Order], int]:
        """注文を検索（戻り値: (注文一覧, 総件数)）"""
        # 総件数を取得
        total_count = await self.count(filters=filter)

        # ページネーション計算
        offset = (page - 1) * limit

        # 注文日時で降順
        order_by = ("ordered_at", True)

        # データを取得
        orders = await self.find(
            filters=filter, order_by=order_by, limit=limit, offset=offset
        )

        return orders, total_count

    async def find_by_date_range(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> list[Order]:
        """期間指定で注文一覧を取得"""
        # 日付を正規化（日の開始と終了時刻に設定）
        date_from_normalized = date_from.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        date_to_normalized = date_to.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # For date ranges, we need to get all user orders and filter manually
        # since the current filter system doesn't support multiple conditions on the same field
        all_orders = await self.find(filters={"user_id": (FilterOp.EQ, user_id)})

        # Filter by date range manually
        filtered_orders = [
            order
            for order in all_orders
            if date_from_normalized <= order.ordered_at <= date_to_normalized
        ]

        # Sort by ordered_at descending
        filtered_orders.sort(key=lambda x: x.ordered_at, reverse=True)

        return filtered_orders

    async def find_completed_by_date(
        self, target_date: datetime, user_id: UUID
    ) -> list[Order]:
        """指定日の完了注文を取得"""
        # 日付を正規化（日の開始と終了時刻に設定）
        date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = target_date.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # 完了ステータスのユーザー注文を取得してから日付でフィルタ
        filters = {
            "user_id": (FilterOp.EQ, user_id),
            "status": (FilterOp.EQ, OrderStatus.COMPLETED),
        }

        all_completed_orders = await self.find(filters=filters)

        # 指定日の完了注文をフィルタ（completed_atで判定）
        completed_orders = [
            order
            for order in all_completed_orders
            if order.completed_at and date_start <= order.completed_at <= date_end
        ]

        # 完了日時で降順
        completed_orders.sort(
            key=lambda x: x.completed_at or x.ordered_at, reverse=True
        )

        return completed_orders

    async def count_by_status_and_date(
        self, target_date: datetime, user_id: UUID
    ) -> dict[OrderStatus, int]:
        """指定日のステータス別注文数を取得"""
        # 日付を正規化（日の開始と終了時刻に設定）
        date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = target_date.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # ユーザーの全注文を取得
        filters = {"user_id": (FilterOp.EQ, user_id)}
        all_orders = await self.find(filters=filters)

        # 指定日の注文をフィルタ
        target_date_orders = [
            order for order in all_orders if date_start <= order.ordered_at <= date_end
        ]

        # ステータス別に集計
        status_counts = {status: 0 for status in OrderStatus}
        for order in target_date_orders:
            status_counts[order.status] += 1

        return status_counts

    async def generate_next_order_number(self, user_id: UUID) -> str:
        """次の注文番号を生成"""
        # 今日の日付を取得
        today = datetime.now().date()
        today_prefix = today.strftime("%Y%m%d")

        # 今日のユーザー注文を取得
        filters = {"user_id": (FilterOp.EQ, user_id)}
        all_orders = await self.find(filters=filters)

        # 今日の注文をフィルタ
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        today_orders = [
            order
            for order in all_orders
            if today_start <= order.ordered_at <= today_end
        ]

        # 今日の注文数を基に次の番号を生成
        next_number = len(today_orders) + 1

        return f"{today_prefix}-{next_number:03d}"

    async def find_orders_by_completion_time_range(
        self, start_time: datetime, end_time: datetime, user_id: UUID
    ) -> list[Order]:
        """完了時間範囲で注文を取得（調理時間分析用）"""
        # 完了した注文のみを取得
        filters = {
            "user_id": (FilterOp.EQ, user_id),
            "status": (FilterOp.EQ, OrderStatus.COMPLETED),
        }

        all_completed_orders = await self.find(filters=filters)

        # 完了時間でフィルタ
        filtered_orders = [
            order
            for order in all_completed_orders
            if order.completed_at and start_time <= order.completed_at <= end_time
        ]

        # 完了時間で昇順ソート（分析用）
        filtered_orders.sort(key=lambda x: x.completed_at or x.ordered_at)

        return filtered_orders


class OrderItemRepository(CrudRepository[OrderItem, UUID]):
    """注文明細リポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, OrderItem)

    async def find_by_order_id(self, order_id: UUID) -> list[OrderItem]:
        """注文IDに紐づく明細一覧を取得"""
        filters = {"order_id": (FilterOp.EQ, order_id)}

        # 作成順でソート
        order_by = ("created_at", False)

        return await self.find(filters=filters, order_by=order_by)

    async def find_existing_item(
        self, order_id: UUID, menu_item_id: UUID
    ) -> OrderItem | None:
        """注文内の既存アイテムを取得（重複チェック用）"""
        filters = {
            "order_id": (FilterOp.EQ, order_id),
            "menu_item_id": (FilterOp.EQ, menu_item_id),
        }

        results = await self.find(filters=filters, limit=1)
        return results[0] if results else None

    async def delete_by_order_id(self, order_id: UUID) -> bool:
        """注文IDに紐づく明細を全削除"""
        # 対象の明細を取得
        filters = {"order_id": (FilterOp.EQ, order_id)}
        order_items = await self.find(filters=filters)

        if not order_items:
            return True  # 削除対象がなければ成功とみなす

        # 一括削除でパフォーマンス向上
        item_ids = [item.id for item in order_items if item.id]
        if item_ids:
            try:
                await self.bulk_delete(item_ids)
                return True
            except Exception:
                return False

        return True

    async def find_by_menu_item_and_date_range(
        self, menu_item_id: UUID, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> list[OrderItem]:
        """期間内の特定メニューアイテムの注文明細を取得"""
        # 日付を正規化
        date_from_normalized = date_from.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        date_to_normalized = date_to.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # 指定メニューアイテムとユーザーでフィルタ
        filters = {
            "menu_item_id": (FilterOp.EQ, menu_item_id),
            "user_id": (FilterOp.EQ, user_id),
        }

        all_items = await self.find(filters=filters)

        # 作成日時で期間フィルタ
        filtered_items = [
            item
            for item in all_items
            if item.created_at
            and date_from_normalized <= item.created_at <= date_to_normalized
        ]

        # 作成日時で降順ソート
        filtered_items.sort(key=lambda x: x.created_at or datetime.min, reverse=True)

        return filtered_items

    async def get_menu_item_sales_summary(
        self, days: int, user_id: UUID
    ) -> list[dict[str, Any]]:
        """メニューアイテム別売上集計を取得"""
        # 過去N日間の日付範囲を計算
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 日付を正規化
        start_date_normalized = start_date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date_normalized = end_date.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # ユーザーの全注文明細を取得
        filters = {"user_id": (FilterOp.EQ, user_id)}
        all_items = await self.find(filters=filters)

        # 期間内の明細をフィルタ
        filtered_items = [
            item
            for item in all_items
            if item.created_at
            and start_date_normalized <= item.created_at <= end_date_normalized
        ]

        # メニューアイテム別に集計
        sales_summary = defaultdict(lambda: {"total_quantity": 0, "total_amount": 0})

        for item in filtered_items:
            menu_item_id = str(item.menu_item_id)
            sales_summary[menu_item_id]["total_quantity"] += item.quantity
            sales_summary[menu_item_id]["total_amount"] += item.subtotal

        # 結果を辞書のリストに変換
        result = []
        for menu_item_id, summary in sales_summary.items():
            result.append(
                {
                    "menu_item_id": menu_item_id,
                    "total_quantity": summary["total_quantity"],
                    "total_amount": summary["total_amount"],
                }
            )

        # 売上金額の降順でソート
        result.sort(key=lambda x: x["total_amount"], reverse=True)

        return result
