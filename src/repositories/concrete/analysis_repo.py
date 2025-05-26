from datetime import datetime


# 仮インターフェース
class IKitchenStatusRepository(ICRUDRepository[KitchenStatus], ABC):
    """キッチン状況リポジトリ"""

    @abstractmethod
    async def find_latest(self, user_id: UUID) -> Optional[KitchenStatus]:
        """最新のキッチン状況を取得"""
        pass

    @abstractmethod
    async def find_by_date_range(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> List[KitchenStatus]:
        """期間指定でキッチン状況履歴を取得"""
        pass


class IDailySummaryRepository(ICRUDRepository[DailySummary], ABC):
    """日別集計リポジトリ"""

    @abstractmethod
    async def find_by_date(
        self, target_date: datetime, user_id: UUID
    ) -> Optional[DailySummary]:
        """指定日の集計を取得"""
        pass

    @abstractmethod
    async def find_by_date_range(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> List[DailySummary]:
        """期間指定で集計一覧を取得"""
        pass
