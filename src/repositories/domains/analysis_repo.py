from datetime import datetime
from uuid import UUID

from constants.options import FilterOp
from models.domains.analytics import DailySummary
from repositories.bases.crud_repo import CrudRepository
from services.platform.client_service import SupabaseClient


class DailySummaryRepository(CrudRepository[DailySummary, UUID]):
    """日別集計リポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, DailySummary)

    async def find_by_date(
        self, target_date: datetime, user_id: UUID
    ) -> DailySummary | None:
        """指定日の集計を取得"""

        # 日付を日の開始時刻に正規化（時分秒をゼロに）
        target_date_normalized = target_date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # ユーザーIDと日付でフィルタ
        filters = {
            "user_id": (FilterOp.EQ, user_id),
            "summary_date": (FilterOp.EQ, target_date_normalized),
        }

        results = await self.find(filters=filters, limit=1)
        return results[0] if results else None

    async def find_by_date_range(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> list[DailySummary]:
        """期間指定で集計一覧を取得"""

        # 開始日を日の開始時刻に、終了日を日の終了時刻に正規化
        date_from_normalized = date_from.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        date_to_normalized = date_to.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # ユーザーIDと日付範囲でフィルタ
        filters = {
            "user_id": (FilterOp.EQ, user_id),
            "summary_date": (FilterOp.GTE, date_from_normalized),
        }

        # 開始日以降の全レコードを取得
        all_results = await self.find(filters=filters)

        # 終了日以前のレコードをフィルタして返す
        filtered_results = [
            result
            for result in all_results
            if result.summary_date <= date_to_normalized
        ]

        # 日付順にソート
        return sorted(filtered_results, key=lambda x: x.summary_date)
