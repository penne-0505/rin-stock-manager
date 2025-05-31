from datetime import datetime
from uuid import UUID

from models.bases._base import CoreBaseModel


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
