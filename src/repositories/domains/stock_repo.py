from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from constants.options import FilterOp
from models.domains.stock import Purchase, PurchaseItem, StockAdjustment, StockTransaction
from repositories.bases.crud_repo import CrudRepository
from services.platform.client_service import SupabaseClient


# 仮インターフェース
class PurchaseRepository(CrudRepository[Purchase, UUID]):
    """仕入れリポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, Purchase)

    async def find_recent(self, days: int, user_id: UUID) -> list[Purchase]:
        """最近の仕入れ一覧を取得"""
        # 過去N日間の開始日を計算
        start_date = datetime.now() - timedelta(days=days)
        start_date_normalized = start_date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # ユーザーの全仕入れを取得
        filters = {"user_id": (FilterOp.EQ, user_id)}
        all_purchases = await self.find(filters=filters)

        # 期間でフィルタ
        recent_purchases = [
            purchase
            for purchase in all_purchases
            if purchase.purchase_date >= start_date_normalized
        ]

        # 仕入れ日で降順ソート
        recent_purchases.sort(key=lambda x: x.purchase_date, reverse=True)

        return recent_purchases

    async def find_by_date_range(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> list[Purchase]:
        """期間指定で仕入れ一覧を取得"""
        # 日付を正規化
        date_from_normalized = date_from.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        date_to_normalized = date_to.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # ユーザーの全仕入れを取得
        filters = {"user_id": (FilterOp.EQ, user_id)}
        all_purchases = await self.find(filters=filters)

        # 期間でフィルタ
        filtered_purchases = [
            purchase
            for purchase in all_purchases
            if date_from_normalized <= purchase.purchase_date <= date_to_normalized
        ]

        # 仕入れ日で降順ソート
        filtered_purchases.sort(key=lambda x: x.purchase_date, reverse=True)

        return filtered_purchases


class PurchaseItemRepository(CrudRepository[PurchaseItem, UUID]):
    """仕入れ明細リポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, PurchaseItem)

    async def find_by_purchase_id(self, purchase_id: UUID) -> list[PurchaseItem]:
        """仕入れIDで明細一覧を取得"""
        filters = {"purchase_id": (FilterOp.EQ, purchase_id)}

        # 作成順でソート
        order_by = ("created_at", False)

        return await self.find(filters=filters, order_by=order_by)

    async def create_batch(
        self, purchase_items: list[PurchaseItem]
    ) -> list[PurchaseItem]:
        """仕入れ明細を一括作成"""
        return await self.bulk_create(purchase_items)


class StockAdjustmentRepository(CrudRepository[StockAdjustment, UUID]):
    """在庫調整リポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, StockAdjustment)

    async def find_by_material_id(
        self, material_id: UUID, user_id: UUID
    ) -> list[StockAdjustment]:
        """材料IDで調整履歴を取得"""
        filters = {
            "material_id": (FilterOp.EQ, material_id),
            "user_id": (FilterOp.EQ, user_id),
        }

        # 調整日時で降順ソート
        order_by = ("adjusted_at", True)

        return await self.find(filters=filters, order_by=order_by)

    async def find_recent(self, days: int, user_id: UUID) -> list[StockAdjustment]:
        """最近の調整履歴を取得"""
        # 過去N日間の開始日を計算
        start_date = datetime.now() - timedelta(days=days)
        start_date_normalized = start_date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # ユーザーの全調整履歴を取得
        filters = {"user_id": (FilterOp.EQ, user_id)}
        all_adjustments = await self.find(filters=filters)

        # 期間でフィルタ
        recent_adjustments = [
            adjustment
            for adjustment in all_adjustments
            if adjustment.adjusted_at >= start_date_normalized
        ]

        # 調整日時で降順ソート
        recent_adjustments.sort(key=lambda x: x.adjusted_at, reverse=True)

        return recent_adjustments


class StockTransactionRepository(CrudRepository[StockTransaction, UUID]):
    """在庫取引リポジトリ"""

    def __init__(self, client: SupabaseClient):
        super().__init__(client, StockTransaction)

    async def create_batch(
        self, transactions: list[StockTransaction]
    ) -> list[StockTransaction]:
        """在庫取引を一括作成"""
        return await self.bulk_create(transactions)

    async def find_by_reference(
        self, reference_type: str, reference_id: UUID, user_id: UUID
    ) -> list[StockTransaction]:
        """参照タイプ・IDで取引履歴を取得"""
        filters = {
            "reference_type": (FilterOp.EQ, reference_type),
            "reference_id": (FilterOp.EQ, reference_id),
            "user_id": (FilterOp.EQ, user_id),
        }

        # 作成日時で降順ソート
        order_by = ("created_at", True)

        return await self.find(filters=filters, order_by=order_by)

    async def find_by_material_and_date_range(
        self, material_id: UUID, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> list[StockTransaction]:
        """材料IDと期間で取引履歴を取得"""
        # 日付を正規化
        date_from_normalized = date_from.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        date_to_normalized = date_to.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # 材料IDとユーザーでフィルタ
        filters = {
            "material_id": (FilterOp.EQ, material_id),
            "user_id": (FilterOp.EQ, user_id),
        }

        all_transactions = await self.find(filters=filters)

        # 作成日時で期間フィルタ
        filtered_transactions = [
            transaction
            for transaction in all_transactions
            if transaction.created_at
            and date_from_normalized <= transaction.created_at <= date_to_normalized
        ]

        # 作成日時で降順ソート
        filtered_transactions.sort(
            key=lambda x: x.created_at or datetime.min, reverse=True
        )

        return filtered_transactions

    async def find_consumption_transactions(
        self, date_from: datetime, date_to: datetime, user_id: UUID
    ) -> list[StockTransaction]:
        """期間内の消費取引（負の値）を取得"""
        # 日付を正規化
        date_from_normalized = date_from.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        date_to_normalized = date_to.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # ユーザーの全取引を取得
        filters = {"user_id": (FilterOp.EQ, user_id)}
        all_transactions = await self.find(filters=filters)

        # 期間内の消費取引（負の値）をフィルタ
        consumption_transactions = [
            transaction
            for transaction in all_transactions
            if (
                transaction.created_at
                and date_from_normalized <= transaction.created_at <= date_to_normalized
                and transaction.change_amount < Decimal("0")
            )
        ]

        # 作成日時で降順ソート
        consumption_transactions.sort(
            key=lambda x: x.created_at or datetime.min, reverse=True
        )

        return consumption_transactions
