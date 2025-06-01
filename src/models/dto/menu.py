from uuid import UUID

from models.bases._base import CoreBaseModel


class MenuAvailabilityInfo(CoreBaseModel):
    """メニュー在庫可否情報"""

    menu_item_id: UUID
    is_available: bool
    missing_materials: list[str] = []  # 不足材料名のリスト
    estimated_servings: int | None = None  # 作れる数量

    @classmethod
    def __table_name__(cls) -> str:
        raise NotImplementedError(
            "MenuAvailabilityInfo is a DTO and does not map to a database table."
        )
