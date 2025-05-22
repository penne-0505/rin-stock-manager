from uuid import UUID

from constants.order_status import OrderStatus
from constants.payment_method import PaymentMethod
from models.order import Order, OrderItem


class OrderService:
    def create_order(
        self,
        items: list[OrderItem],
        discount_amount: int | None = None,
    ) -> Order:
        """新規注文を作成する"""

    def get_order(self, order_id: UUID) -> Order | None:
        """注文情報を取得する"""

    def list_orders(self, status: OrderStatus | None = None) -> list[Order]:
        """注文一覧を取得（ステータスによる絞り込みも可能）"""

    def update_order_status(self, order_id: UUID, status: OrderStatus) -> None:
        """注文の状態を更新する（準備中/提供済み/キャンセル済み）"""

    def add_item_to_order(self, order_id: UUID, item: OrderItem) -> None:
        """注文に商品を追加する"""

    def remove_item_from_order(self, order_id: UUID, inventory_item_id: UUID) -> None:
        """注文から商品を削除する"""

    def record_payment(self, order_id: UUID, payment_method: PaymentMethod) -> None:
        """注文に支払方法を記録する"""
