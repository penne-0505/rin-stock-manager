from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from models.bases._base import CoreBaseModel


class StockUpdateRequest(CoreBaseModel):
    """在庫更新リクエスト"""

    material_id: UUID
    new_quantity: Decimal
    reason: str
    notes: str | None = None

    @classmethod
    def __table_name__(cls) -> str:
        raise NotImplementedError(
            "StockUpdateRequest is a DTO and does not map to a database table."
        )


class PurchaseRequest(CoreBaseModel):
    """仕入れリクエスト"""

    items: list[PurchaseItemDto]
    purchase_date: datetime
    notes: str | None = None

    @classmethod
    def __table_name__(cls) -> str:
        raise NotImplementedError(
            "PurchaseRequest is a DTO and does not map to a database table."
        )


class PurchaseItemDto(CoreBaseModel):
    """仕入れアイテムDTO"""

    material_id: UUID
    quantity: Decimal

    @classmethod
    def __table_name__(cls) -> str:
        raise NotImplementedError(
            "PurchaseItemDto is a DTO and does not map to a database table."
        )
