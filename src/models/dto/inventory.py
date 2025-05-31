from decimal import Decimal
from uuid import UUID

from constants.options import StockLevel
from models.bases._base import CoreBaseModel
from models.domains.inventory import Material


class MaterialStockInfo(CoreBaseModel):
    """材料在庫情報（在庫レベル付き）"""

    material: Material
    stock_level: StockLevel
    estimated_usage_days: int | None
    daily_usage_rate: Decimal | None

    @classmethod
    def __table_name__(cls) -> str:
        raise NotImplementedError(
            "MaterialStockInfo is a DTO and does not map to a database table."
        )


class MaterialUsageCalculation(CoreBaseModel):
    """材料使用量計算結果"""

    material_id: UUID
    required_amount: Decimal
    available_amount: Decimal
    is_sufficient: bool

    @classmethod
    def __table_name__(cls) -> str:
        raise NotImplementedError(
            "MaterialUsageCalculation is a DTO and does not map to a database table."
        )
