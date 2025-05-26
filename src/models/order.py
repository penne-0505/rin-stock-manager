from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from constants.options import PaymentMethod
from constants.status import OrderStatus
from models._base import CoreBaseModel

# ============================================================================
# Domain Models
# ============================================================================


class Order(CoreBaseModel):
    """注文"""

    id: UUID | None = None
    total_amount: int  # 合計金額
    status: OrderStatus  # 注文ステータス
    payment_method: PaymentMethod  # 支払い方法
    discount_amount: int = 0  # 割引額
    customer_name: str | None = None  # 顧客名（呼び出し用）
    notes: str | None = None  # 備考
    ordered_at: datetime  # 注文日時
    started_preparing_at: datetime | None = None  # 調理開始日時
    ready_at: datetime | None = None  # 完成日時
    completed_at: datetime | None = None  # 提供完了日時
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    def __table_name__(self) -> str:
        return "orders"


class OrderItem(CoreBaseModel):
    """注文明細"""

    id: UUID | None = None
    order_id: UUID  # 注文ID
    menu_item_id: UUID  # メニューID
    quantity: int  # 数量
    unit_price: int  # 単価（注文時点の価格）
    subtotal: int  # 小計
    selected_options: dict[str, str] | None = None  # 選択されたオプション
    special_request: str | None = None  # 特別リクエスト(例: アレルギー対応)
    created_at: datetime | None = None
    user_id: UUID | None = None

    def __table_name__(self) -> str:
        return "order_items"


# ============================================================================
# DTO and Request Models
# ============================================================================


@dataclass
class CartItemRequest:
    """カートアイテム追加/更新リクエスト"""

    menu_item_id: UUID
    quantity: int
    selected_options: dict[str, str] | None = None
    special_request: str | None = None


@dataclass
class OrderCheckoutRequest:
    """注文確定リクエスト"""

    payment_method: PaymentMethod
    customer_name: str | None = None
    discount_amount: int = 0
    notes: str | None = None


@dataclass
class OrderSearchRequest:
    """注文検索リクエスト"""

    date_from: datetime | None = None
    date_to: datetime | None = None
    status_filter: list[OrderStatus] | None = None
    customer_name: str | None = None
    menu_item_name: str | None = None
    page: int = 1
    limit: int = 20


@dataclass
class OrderCalculationResult:
    """注文金額計算結果"""

    subtotal: int
    tax_amount: int
    discount_amount: int
    total_amount: int
