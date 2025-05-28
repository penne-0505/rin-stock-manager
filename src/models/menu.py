from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from models._base import CoreBaseModel

# ============================================================================
# Domain Models
# ============================================================================


class MenuCategory(CoreBaseModel):
    """メニューカテゴリ"""

    id: UUID | None = None
    name: str  # カテゴリ名（メイン料理、サイドメニュー、ドリンク、デザート）
    display_order: int = 0  # 表示順序
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    @classmethod
    def __table_name__(cls) -> str:
        return "menu_categories"


class MenuItem(CoreBaseModel):
    """メニュー（販売商品）"""

    id: UUID | None = None
    name: str  # 商品名
    category_id: UUID  # メニューカテゴリID
    price: int  # 販売価格（円）
    description: str | None = None  # 商品説明
    is_available: bool = True  # 販売可能フラグ
    estimated_prep_time_minutes: int = 5  # 推定調理時間（分）
    display_order: int = 0  # 表示順序
    image_url: str | None = None  # 商品画像URL
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    @classmethod
    def __table_name__(cls) -> str:
        return "menu_items"


class MenuItemOption(CoreBaseModel):
    """メニューオプション（トッピングなど）"""

    id: UUID | None = None
    menu_item_id: UUID  # メニューID
    option_name: str  # オプション名（例：「ソース」）
    option_values: list[str]  # 選択肢（例：["あり", "なし"]）
    is_required: bool = False  # 必須選択かどうか
    additional_price: int = 0  # 追加料金
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    @classmethod
    def __table_name__(cls) -> str:
        return "menu_item_options"


# ============================================================================
# DTO and Request Models
# ============================================================================


@dataclass
class MenuAvailabilityInfo:
    """メニュー在庫可否情報"""

    menu_item_id: UUID
    is_available: bool
    missing_materials: list[str] = field(default_factory=list)  # 不足材料名のリスト
    estimated_servings: int | None = None  # 作れる数量
