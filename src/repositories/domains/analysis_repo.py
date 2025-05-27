from services.platform.client_service import SupabaseClient
from uuid import UUID
from datetime import datetime
from repositories.bases.crud_repo import CrudRepository
from models.analytics import DailySummary


class DailySummaryRepository(CrudRepository[DailySummary, UUID]):
    """日別集計リポジトリ"""
    def __init__(self, client: SupabaseClient):
        super().__init__(client, DailySummary)

    async def find_by_date(
        self, target_date: datetime, user_id: UUID
    ) -> DailySummary | None:
        """指定日の集計を取得"""
        pass

    async def find_by_date_range(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> list[DailySummary]:
        """期間指定で集計一覧を取得"""
        pass
