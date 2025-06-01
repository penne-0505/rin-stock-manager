from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from constants.status import OrderStatus
from models.dto.analytics import DailyStatsResult
from repositories.domains.analysis_repo import DailySummaryRepository
from repositories.domains.order_repo import OrderItemRepository, OrderRepository
from repositories.domains.stock_repo import StockTransactionRepository
from services.platform.client_service import SupabaseClient


class AnalyticsService:
    """分析・統計サービス"""

    def __init__(self, client: SupabaseClient):
        self.daily_summary_repo = DailySummaryRepository(client)
        self.order_repo = OrderRepository(client)
        self.order_item_repo = OrderItemRepository(client)
        self.stock_transaction_repo = StockTransactionRepository(client)

    async def get_real_time_daily_stats(
        self, target_date: datetime, user_id: UUID
    ) -> DailyStatsResult:
        """リアルタイム日次統計を取得"""

        # 指定日の注文数を取得
        status_counts = await self.order_repo.count_by_status_and_date(
            target_date, user_id
        )

        # 完了注文を取得して売上計算
        completed_orders = await self.order_repo.find_completed_by_date(
            target_date, user_id
        )
        total_revenue = sum(order.total_amount for order in completed_orders)

        # 平均調理時間を計算
        prep_times = []
        for order in completed_orders:
            if order.started_preparing_at and order.ready_at:
                delta = order.ready_at - order.started_preparing_at
                prep_times.append(int(delta.total_seconds() / 60))

        average_prep_time = (
            int(sum(prep_times) / len(prep_times)) if prep_times else None
        )

        # 最人気商品を取得
        popular_items = await self.get_popular_items_ranking(1, 1, user_id)
        most_popular_item = popular_items[0] if popular_items else None

        return DailyStatsResult(
            completed_orders=status_counts.get(OrderStatus.COMPLETED, 0),
            pending_orders=status_counts.get(OrderStatus.PREPARING, 0),
            total_revenue=total_revenue,
            average_prep_time_minutes=average_prep_time,
            most_popular_item=most_popular_item,
        )

    async def get_popular_items_ranking(
        self, days: int, limit: int, user_id: UUID
    ) -> list[dict[str, Any]]:
        """人気商品ランキングを取得"""
        # 売上集計を取得
        sales_summary = await self.order_item_repo.get_menu_item_sales_summary(
            days, user_id
        )

        # 上位N件を取得
        top_items = sales_summary[:limit]

        # 結果を整形
        ranking = []
        for i, item in enumerate(top_items):
            ranking.append(
                {
                    "rank": i + 1,
                    "menu_item_id": item["menu_item_id"],
                    "total_quantity": item["total_quantity"],
                    "total_amount": item["total_amount"],
                }
            )

        return ranking

    async def calculate_average_preparation_time(
        self, days: int, menu_item_id: UUID | None, user_id: UUID
    ) -> float | None:
        """平均調理時間を計算"""

        # 期間を計算
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 完了注文を取得
        completed_orders = await self.order_repo.find_orders_by_completion_time_range(
            start_date, end_date, user_id
        )

        # 特定メニューアイテムの場合はフィルタ
        if menu_item_id:
            # 該当メニューアイテムを含む注文のみ抽出
            filtered_orders = []
            for order in completed_orders:
                order_items = await self.order_item_repo.find_by_order_id(order.id)
                if any(item.menu_item_id == menu_item_id for item in order_items):
                    filtered_orders.append(order)
            completed_orders = filtered_orders

        # 調理時間を計算
        prep_times = []
        for order in completed_orders:
            if order.started_preparing_at and order.ready_at:
                delta = order.ready_at - order.started_preparing_at
                prep_times.append(delta.total_seconds() / 60)  # 分単位

        return sum(prep_times) / len(prep_times) if prep_times else None

    async def get_hourly_order_distribution(
        self, target_date: datetime, user_id: UUID
    ) -> dict[int, int]:
        """時間帯別注文分布を取得"""
        # 指定日の全注文を取得
        orders = await self.order_repo.find_by_date_range(
            target_date, target_date, user_id
        )

        # 時間帯別に集計
        hourly_distribution = defaultdict(int)
        for order in orders:
            hour = order.ordered_at.hour
            hourly_distribution[hour] += 1

        # 0-23時まで全時間を含むdictを作成
        result = {hour: hourly_distribution[hour] for hour in range(24)}

        return result

    async def calculate_revenue_by_date_range(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> dict[str, Any]:
        """期間指定売上を計算"""

        # 期間内の完了注文を取得
        orders = await self.order_repo.find_by_date_range(date_from, date_to, user_id)
        completed_orders = [
            order for order in orders if order.status == OrderStatus.COMPLETED
        ]

        # 売上計算
        total_revenue = sum(order.total_amount for order in completed_orders)
        total_orders = len(completed_orders)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0

        # 日別売上を計算
        daily_revenue = defaultdict(int)
        for order in completed_orders:
            date_key = (
                order.completed_at.date().isoformat()
                if order.completed_at
                else order.ordered_at.date().isoformat()
            )
            daily_revenue[date_key] += order.total_amount

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "average_order_value": average_order_value,
            "daily_breakdown": dict(daily_revenue),
            "period_start": date_from.isoformat(),
            "period_end": date_to.isoformat(),
        }

    async def get_material_consumption_analysis(
        self, material_id: UUID, days: int, user_id: UUID
    ) -> dict[str, Any]:
        """材料消費分析を取得"""
        # 期間を計算
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 材料の消費取引を取得
        transactions = (
            await self.stock_transaction_repo.find_by_material_and_date_range(
                material_id, start_date, end_date, user_id
            )
        )

        # 消費取引のみを抽出（負の値）
        from decimal import Decimal

        consumption_transactions = [
            tx for tx in transactions if tx.change_amount < Decimal("0")
        ]

        # 統計を計算
        total_consumed = sum(abs(tx.change_amount) for tx in consumption_transactions)
        daily_consumption = defaultdict(Decimal)

        for tx in consumption_transactions:
            date_key = (
                tx.created_at.date().isoformat()
                if tx.created_at
                else datetime.now().date().isoformat()
            )
            daily_consumption[date_key] += abs(tx.change_amount)

        average_daily_consumption = total_consumed / days if days > 0 else Decimal("0")

        return {
            "material_id": str(material_id),
            "analysis_period_days": days,
            "total_consumed": float(total_consumed),
            "average_daily_consumption": float(average_daily_consumption),
            "daily_breakdown": {k: float(v) for k, v in daily_consumption.items()},
            "consumption_events": len(consumption_transactions),
        }

    async def calculate_menu_item_profitability(
        self, menu_item_id: UUID, days: int, user_id: UUID
    ) -> dict[str, Any]:
        """メニューアイテムの収益性を分析"""
        # 期間を計算
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 指定メニューアイテムの注文明細を取得
        order_items = await self.order_item_repo.find_by_menu_item_and_date_range(
            menu_item_id, start_date, end_date, user_id
        )

        # 売上統計を計算
        total_quantity = sum(item.quantity for item in order_items)
        total_revenue = sum(item.subtotal for item in order_items)
        average_price = total_revenue / total_quantity if total_quantity > 0 else 0

        # 日別売上を計算
        daily_sales = defaultdict(lambda: {"quantity": 0, "revenue": 0})
        for item in order_items:
            date_key = (
                item.created_at.date().isoformat()
                if item.created_at
                else datetime.now().date().isoformat()
            )
            daily_sales[date_key]["quantity"] += item.quantity
            daily_sales[date_key]["revenue"] += item.subtotal

        return {
            "menu_item_id": str(menu_item_id),
            "analysis_period_days": days,
            "total_quantity_sold": total_quantity,
            "total_revenue": total_revenue,
            "average_selling_price": average_price,
            "daily_breakdown": dict(daily_sales),
            "average_daily_quantity": total_quantity / days if days > 0 else 0,
        }

    async def get_daily_summary_with_trends(
        self, target_date: datetime, comparison_days: int, user_id: UUID
    ) -> dict[str, Any]:
        """日次サマリーをトレンド比較付きで取得"""
        # 対象日の統計を取得
        target_stats = await self.get_real_time_daily_stats(target_date, user_id)

        # 比較期間の統計を取得
        comparison_start = target_date - timedelta(days=comparison_days)
        comparison_end = target_date - timedelta(days=1)

        comparison_revenue = await self.calculate_revenue_by_date_range(
            comparison_start, comparison_end, user_id
        )

        # トレンド計算
        avg_daily_revenue = (
            comparison_revenue["total_revenue"] / comparison_days
            if comparison_days > 0
            else 0
        )
        revenue_trend = (
            ((target_stats.total_revenue - avg_daily_revenue) / avg_daily_revenue * 100)
            if avg_daily_revenue > 0
            else 0
        )

        avg_daily_orders = (
            comparison_revenue["total_orders"] / comparison_days
            if comparison_days > 0
            else 0
        )
        order_trend = (
            (
                (target_stats.completed_orders - avg_daily_orders)
                / avg_daily_orders
                * 100
            )
            if avg_daily_orders > 0
            else 0
        )

        return {
            "target_date": target_date.date().isoformat(),
            "current_stats": {
                "completed_orders": target_stats.completed_orders,
                "pending_orders": target_stats.pending_orders,
                "total_revenue": target_stats.total_revenue,
                "average_prep_time_minutes": target_stats.average_prep_time_minutes,
                "most_popular_item": target_stats.most_popular_item,
            },
            "trends": {
                "revenue_change_percent": round(revenue_trend, 2),
                "order_count_change_percent": round(order_trend, 2),
                "comparison_period_days": comparison_days,
            },
            "comparison_averages": {
                "avg_daily_revenue": round(avg_daily_revenue, 2),
                "avg_daily_orders": round(avg_daily_orders, 2),
            },
        }
