from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from models._base import CoreBaseModel

# ============================================================================
# Domain Models
# ============================================================================


class DailySummary(CoreBaseModel):
    """日別集計"""

    id: UUID | None = None
    summary_date: datetime  # 集計日
    total_orders: int  # 総注文数
    completed_orders: int  # 完了注文数
    pending_orders: int  # 進行中注文数
    total_revenue: int  # 総売上
    average_prep_time_minutes: int | None = None  # 平均調理時間
    most_popular_item_id: UUID | None = None  # 最人気商品ID
    most_popular_item_count: int = 0  # 最人気商品販売数
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_id: UUID | None = None

    @classmethod
    def __table_name__(cls) -> str:
        return "daily_summaries"


# ============================================================================
# DTO and Request Models
# ============================================================================


@dataclass
class DailyStatsResult:
    """日次統計結果"""

    completed_orders: int
    pending_orders: int
    total_revenue: int
    average_prep_time_minutes: int | None
    most_popular_item: dict[str, Any] | None
