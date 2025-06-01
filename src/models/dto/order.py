from datetime import datetime
from uuid import UUID

from constants.options import PaymentMethod
from constants.status import OrderStatus
from models.bases._base import CoreBaseModel


class CartItemRequest(CoreBaseModel):
    """カートアイテム追加/更新リクエスト"""

    menu_item_id: UUID
    quantity: int
    selected_options: dict[str, str] | None = None
    special_request: str | None = None

    @classmethod
    def __table_name__(cls) -> str:
        raise NotImplementedError(
            "CartItemRequest is a DTO and does not map to a database table."
        )


class OrderCheckoutRequest(CoreBaseModel):
    """注文確定リクエスト"""

    payment_method: PaymentMethod
    customer_name: str | None = None
    discount_amount: int = 0
    notes: str | None = None

    @classmethod
    def __table_name__(cls) -> str:
        raise NotImplementedError(
            "OrderCheckoutRequest is a DTO and does not map to a database table."
        )


class OrderSearchRequest(CoreBaseModel):
    """注文検索リクエスト"""

    date_from: datetime | None = None
    date_to: datetime | None = None
    status_filter: list[OrderStatus] | None = None
    customer_name: str | None = None
    menu_item_name: str | None = None
    page: int = 1
    limit: int = 20

    @classmethod
    def __table_name__(cls) -> str:
        raise NotImplementedError(
            "OrderSearchRequest is a DTO and does not map to a database table."
        )


class OrderCalculationResult(CoreBaseModel):
    """注文金額計算結果"""

    subtotal: int
    tax_amount: int
    discount_amount: int
    total_amount: int

    @classmethod
    def __table_name__(cls) -> str:
        raise NotImplementedError(
            "OrderCalculationResult is a DTO and does not map to a database table."
        )
