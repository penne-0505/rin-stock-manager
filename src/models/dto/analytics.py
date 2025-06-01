from typing import Any

from models.bases._base import CoreBaseModel


class DailyStatsResult(CoreBaseModel):
    """日次統計結果"""

    completed_orders: int
    pending_orders: int
    total_revenue: int
    average_prep_time_minutes: int | None
    most_popular_item: dict[str, Any] | None

    @classmethod
    def __table_name__(cls) -> str:
        raise NotImplementedError(
            "DailyStatsResult is a DTO and does not map to a database table."
        )