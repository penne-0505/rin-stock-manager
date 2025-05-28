from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from constants.options import StockLevel, UnitType
from models._base import CoreBaseModel

# ============================================================================
# Domain Models
# ============================================================================


class Material(CoreBaseModel):
    """材料マスタ"""

    id: UUID | None = None
    name: str  # 材料名
    category_id: UUID  # 材料カテゴリID
    unit_type: UnitType  # 管理単位（個数 or グラム）
    current_stock: Decimal  # 現在在庫量
    alert_threshold: Decimal  # アラート閾値
    critical_threshold: Decimal  # 緊急閾値
    notes: str | None = None  # メモ
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    @classmethod
    def __table_name__(cls) -> str:
        return "materials"

    def get_stock_level(self) -> StockLevel:
        """在庫レベルを取得"""
        if self.current_stock <= self.critical_threshold:
            return StockLevel.CRITICAL
        elif self.current_stock <= self.alert_threshold:
            return StockLevel.LOW
        else:
            return StockLevel.SUFFICIENT


class MaterialCategory(CoreBaseModel):
    """材料カテゴリ"""

    id: UUID | None = None
    name: str  # カテゴリ名（肉類、野菜、調理済食品、果物）
    display_order: int = 0  # 表示順序
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    @classmethod
    def __table_name__(cls) -> str:
        return "material_categories"


class Recipe(CoreBaseModel):
    """レシピ（メニューと材料の関係）"""

    id: UUID | None = None
    menu_item_id: UUID  # メニューID
    material_id: UUID  # 材料ID
    required_amount: Decimal  # 必要量（材料の単位に依存）
    is_optional: bool = False  # オプション材料かどうか
    notes: str | None = None  # 備考
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    @classmethod
    def __table_name__(cls) -> str:
        return "recipes"


# ============================================================================
# DTO and Request Models
# ============================================================================


@dataclass
class MaterialStockInfo:
    """材料在庫情報（在庫レベル付き）"""

    material: Material
    stock_level: StockLevel
    estimated_usage_days: int | None
    daily_usage_rate: Decimal | None


@dataclass
class MaterialUsageCalculation:
    """材料使用量計算結果"""

    material_id: UUID
    required_amount: Decimal
    available_amount: Decimal
    is_sufficient: bool
