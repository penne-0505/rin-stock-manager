from datetime import datetime
from typing import Any
from uuid import UUID

from constants.status import OrderStatus
from models.order import (
    CartItemRequest,
    Order,
    OrderCalculationResult,
    OrderCheckoutRequest,
    OrderItem,
    OrderSearchRequest,
)


class ICartService:
    """カート（下書き注文）管理サービス"""

    async def get_or_create_active_cart(self, user_id: UUID) -> Order:
        """アクティブなカート（下書き注文）を取得または作成"""
        pass

    async def add_item_to_cart(
        self, cart_id: UUID, request: CartItemRequest, user_id: UUID
    ) -> tuple[OrderItem, bool]:
        """カートに商品を追加（戻り値: (OrderItem, 在庫充足フラグ)）"""
        pass

    async def update_cart_item_quantity(
        self, cart_id: UUID, order_item_id: UUID, new_quantity: int, user_id: UUID
    ) -> tuple[OrderItem, bool]:
        """カート内商品の数量を更新"""
        pass

    async def remove_item_from_cart(
        self, cart_id: UUID, order_item_id: UUID, user_id: UUID
    ) -> bool:
        """カートから商品を削除"""
        pass

    async def clear_cart(self, cart_id: UUID, user_id: UUID) -> bool:
        """カートを空にする"""
        pass

    async def calculate_cart_total(
        self, cart_id: UUID, discount_amount: int = 0
    ) -> OrderCalculationResult:
        """カートの金額を計算"""
        pass

    async def validate_cart_stock(
        self, cart_id: UUID, user_id: UUID
    ) -> dict[UUID, bool]:
        """カート内全商品の在庫を検証（戻り値: {order_item_id: 在庫充足フラグ}）"""
        pass


class IOrderService:
    """注文管理サービス"""

    async def checkout_cart(
        self, cart_id: UUID, request: OrderCheckoutRequest, user_id: UUID
    ) -> tuple[Order, bool]:
        """カートを確定して正式注文に変換（戻り値: (Order, 成功フラグ)）"""
        pass

    async def cancel_order(
        self, order_id: UUID, reason: str, user_id: UUID
    ) -> tuple[Order, bool]:
        """注文をキャンセル（在庫復元含む）"""
        pass

    async def get_order_history(
        self, request: OrderSearchRequest, user_id: UUID
    ) -> dict[str, Any]:
        """注文履歴を取得（ページネーション付き）"""
        pass

    async def get_order_details(self, order_id: UUID, user_id: UUID) -> Order | None:
        """注文詳細を取得"""
        pass

    async def get_order_with_items(
        self, order_id: UUID, user_id: UUID
    ) -> dict[str, Any] | None:
        """注文と注文明細を一括取得"""
        pass


class IKitchenService:
    """調理・キッチン管理サービス"""

    async def get_active_orders_by_status(
        self, user_id: UUID
    ) -> dict[OrderStatus, list[Order]]:
        """ステータス別進行中注文を取得"""
        pass

    async def get_order_queue(self, user_id: UUID) -> list[Order]:
        """注文キューを取得（調理順序順）"""
        pass

    async def start_order_preparation(self, order_id: UUID, user_id: UUID) -> Order:
        """注文の調理を開始"""
        pass

    async def complete_order_preparation(self, order_id: UUID, user_id: UUID) -> Order:
        """注文の調理を完了"""
        pass

    async def mark_order_ready(self, order_id: UUID, user_id: UUID) -> Order:
        """注文を提供準備完了にマーク"""
        pass

    async def deliver_order(self, order_id: UUID, user_id: UUID) -> Order:
        """注文を提供完了"""
        pass

    async def calculate_estimated_completion_time(
        self, order_id: UUID, user_id: UUID
    ) -> datetime | None:
        """完成予定時刻を計算"""
        pass

    async def adjust_estimated_completion_time(
        self, order_id: UUID, additional_minutes: int, user_id: UUID
    ) -> Order:
        """完成予定時刻を調整"""
        pass

    async def update_kitchen_status(
        self, active_staff_count: int, notes: str | None, user_id: UUID
    ) -> bool:
        """キッチン状況を更新"""
        pass

    async def get_kitchen_workload(self, user_id: UUID) -> dict[str, Any]:
        """キッチンの負荷状況を取得"""
        pass

    async def calculate_queue_wait_time(self, user_id: UUID) -> int:
        """注文キューの待ち時間を計算（分）"""
        pass

    async def optimize_cooking_order(self, user_id: UUID) -> list[UUID]:
        """調理順序を最適化（注文IDリストを返す）"""
        pass

    async def predict_completion_times(self, user_id: UUID) -> dict[UUID, datetime]:
        """全注文の完成予定時刻を予測"""
        pass

    async def get_kitchen_performance_metrics(
        self, target_date: datetime, user_id: UUID
    ) -> dict[str, Any]:
        """キッチンパフォーマンス指標を取得"""
        pass


# TODO: Orderモデルに統合されていたビジネスロジック。OrderServiceに移行する。
def get_actual_prep_time_minutes(self) -> int | None:
    """実際の調理時間を取得（分）"""
    if self.started_preparing_at and self.ready_at:
        delta = self.ready_at - self.started_preparing_at
        return int(delta.total_seconds() / 60)
    return None
