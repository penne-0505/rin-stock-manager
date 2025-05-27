from datetime import datetime
from typing import Any
from uuid import UUID

from models.analytics import DailyStatsResult


class IAnalyticsService:
    """分析・統計サービス"""

    async def get_real_time_daily_stats(
        self, target_date: datetime, user_id: UUID
    ) -> DailyStatsResult:
        """リアルタイム日次統計を取得"""
        pass

    async def get_popular_items_ranking(
        self, days: int, limit: int, user_id: UUID
    ) -> list[dict[str, Any]]:
        """人気商品ランキングを取得"""
        pass

    async def calculate_average_preparation_time(
        self, days: int, menu_item_id: UUID | None, user_id: UUID
    ) -> float | None:
        """平均調理時間を計算"""
        pass

    async def get_hourly_order_distribution(
        self, target_date: datetime, user_id: UUID
    ) -> dict[int, int]:
        """時間帯別注文分布を取得"""
        pass

    async def calculate_revenue_by_date_range(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> dict[str, Any]:
        """期間指定売上を計算"""
        pass

    async def get_material_consumption_analysis(
        self, material_id: UUID, days: int, user_id: UUID
    ) -> dict[str, Any]:
        """材料消費分析を取得"""
        pass

    async def calculate_menu_item_profitability(
        self, menu_item_id: UUID, days: int, user_id: UUID
    ) -> dict[str, Any]:
        """メニューアイテムの収益性を分析"""
        pass

    async def get_daily_summary_with_trends(
        self, target_date: datetime, comparison_days: int, user_id: UUID
    ) -> dict[str, Any]:
        """日次サマリーをトレンド比較付きで取得"""
        pass
