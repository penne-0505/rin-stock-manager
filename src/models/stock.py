from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from constants.options import ReferenceType, TransactionType
from models._base import CoreBaseModel

# ============================================================================
# Domain Models
# ============================================================================


class StockTransaction(CoreBaseModel):
    """在庫取引記録"""

    id: UUID | None = None
    material_id: UUID  # 材料ID
    transaction_type: TransactionType  # 取引タイプ
    change_amount: Decimal  # 変動量（正=入庫、負=出庫）
    reference_type: ReferenceType | None = None  # 参照タイプ
    reference_id: UUID | None = None  # 参照ID
    notes: str | None = None  # 備考
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    def __table_name__(self) -> str:
        return "stock_transactions"


class Purchase(CoreBaseModel):
    """仕入れ記録"""

    id: UUID | None = None
    purchase_date: datetime  # 仕入れ日
    notes: str | None = None  # 備考
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    def __table_name__(self) -> str:
        return "purchases"


class PurchaseItem(CoreBaseModel):
    """仕入れ明細"""

    id: UUID | None = None
    purchase_id: UUID  # 仕入れID
    material_id: UUID  # 材料ID
    quantity: Decimal  # 仕入れ量(パッケージ単位)
    created_at: datetime | None = None
    user_id: UUID | None = None

    def __table_name__(self) -> str:
        return "purchase_items"


class StockAdjustment(CoreBaseModel):
    """在庫調整"""

    id: UUID | None = None
    material_id: UUID  # 材料ID
    adjustment_amount: Decimal  # 調整量（正負両方）
    notes: str | None = None  # メモ
    adjusted_at: datetime  # 調整日時
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    def __table_name__(self) -> str:
        return "stock_adjustments"


# ============================================================================
# DTO and Request Models
# ============================================================================


@dataclass
class StockUpdateRequest:
    """在庫更新リクエスト"""

    material_id: UUID
    new_quantity: Decimal
    reason: str
    notes: str | None = None


@dataclass
class PurchaseRequest:
    """仕入れリクエスト"""

    items: list[PurchaseItem]
    purchase_date: datetime
    notes: str | None = None


@dataclass
class PurchaseItem:
    """仕入れアイテム"""

    material_id: UUID
    quantity: Decimal
