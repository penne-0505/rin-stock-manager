from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from constants.options import FilterOp, ReferenceType, TransactionType
from models.inventory import Material, MaterialCategory, MaterialStockInfo, StockLevel
from models.stock import (
    Purchase,
    PurchaseItem,
    PurchaseRequest,
    StockAdjustment,
    StockTransaction,
    StockUpdateRequest,
)
from repositories.domains.inventory_repo import (
    MaterialCategoryRepository,
    MaterialRepository,
    RecipeRepository,
)
from repositories.domains.order_repo import OrderItemRepository
from repositories.domains.stock_repo import (
    PurchaseItemRepository,
    PurchaseRepository,
    StockAdjustmentRepository,
    StockTransactionRepository,
)
from services.platform.client_service import SupabaseClient


class InventoryService:
    """在庫管理サービス"""

    def __init__(self, client: SupabaseClient):
        self.material_repo = MaterialRepository(client)
        self.material_category_repo = MaterialCategoryRepository(client)
        self.recipe_repo = RecipeRepository(client)
        self.purchase_repo = PurchaseRepository(client)
        self.purchase_item_repo = PurchaseItemRepository(client)
        self.stock_adjustment_repo = StockAdjustmentRepository(client)
        self.stock_transaction_repo = StockTransactionRepository(client)
        self.order_item_repo = OrderItemRepository(client)

    async def get_material_categories(self, user_id: UUID) -> list[MaterialCategory]:
        """材料カテゴリ一覧を取得"""
        return await self.material_category_repo.find_active_ordered(user_id)

    async def get_materials_by_category(
        self, category_id: UUID | None, user_id: UUID
    ) -> list[Material]:
        """カテゴリ別材料一覧を取得"""
        return await self.material_repo.find_by_category_id(category_id, user_id)

    async def get_stock_alerts_by_level(
        self, user_id: UUID
    ) -> dict[StockLevel, list[Material]]:
        """在庫レベル別アラート材料を取得"""
        critical_materials = await self.material_repo.find_below_critical_threshold(
            user_id
        )
        alert_materials = await self.material_repo.find_below_alert_threshold(user_id)

        # アラートレベルからクリティカルを除外
        alert_only = [m for m in alert_materials if m not in critical_materials]

        return {
            StockLevel.CRITICAL: critical_materials,
            StockLevel.LOW: alert_only,
            StockLevel.SUFFICIENT: [],
        }

    async def get_critical_stock_materials(self, user_id: UUID) -> list[Material]:
        """緊急レベルの材料一覧を取得"""
        return await self.material_repo.find_below_critical_threshold(user_id)

    async def update_material_stock(
        self, request: StockUpdateRequest, user_id: UUID
    ) -> Material:
        """材料在庫を手動更新"""
        # 材料を取得
        material = await self.material_repo.find_by_id(request.material_id)
        if not material or material.user_id != user_id:
            raise ValueError("Material not found or access denied")

        # 在庫調整を記録
        adjustment_amount = request.new_quantity - material.current_stock
        adjustment = StockAdjustment(
            material_id=request.material_id,
            adjustment_amount=adjustment_amount,
            notes=request.notes,
            adjusted_at=datetime.now(),
            user_id=user_id,
        )
        await self.stock_adjustment_repo.create(adjustment)

        # 在庫取引を記録
        transaction = StockTransaction(
            material_id=request.material_id,
            transaction_type=TransactionType.ADJUSTMENT,
            change_amount=adjustment_amount,
            reference_type=ReferenceType.ADJUSTMENT,
            reference_id=adjustment.id,
            notes=request.reason,
            user_id=user_id,
        )
        await self.stock_transaction_repo.create(transaction)

        # 材料の在庫を更新
        material.current_stock = request.new_quantity
        return await self.material_repo.update(material.id, material)

    async def record_purchase(self, request: PurchaseRequest, user_id: UUID) -> UUID:
        """仕入れを記録し、在庫を増加"""
        # 仕入れを作成
        purchase = Purchase(
            purchase_date=request.purchase_date, notes=request.notes, user_id=user_id
        )
        created_purchase = await self.purchase_repo.create(purchase)

        # 仕入れ明細を作成
        purchase_items = []
        for item_data in request.items:
            item = PurchaseItem(
                purchase_id=created_purchase.id,
                material_id=item_data.material_id,
                quantity=item_data.quantity,
                user_id=user_id,
            )
            purchase_items.append(item)

        await self.purchase_item_repo.create_batch(purchase_items)

        # 各材料の在庫を増加し、取引を記録
        transactions = []
        for item_data in request.items:
            # 材料を取得して在庫更新
            material = await self.material_repo.find_by_id(item_data.material_id)
            if material and material.user_id == user_id:
                material.current_stock += item_data.quantity
                await self.material_repo.update(material.id, material)

                # 取引記録を作成
                transaction = StockTransaction(
                    material_id=item_data.material_id,
                    transaction_type=TransactionType.PURCHASE,
                    change_amount=item_data.quantity,
                    reference_type=ReferenceType.PURCHASE,
                    reference_id=created_purchase.id,
                    user_id=user_id,
                )
                transactions.append(transaction)

        await self.stock_transaction_repo.create_batch(transactions)

        return created_purchase.id

    async def get_materials_with_stock_info(
        self, category_id: UUID | None, user_id: UUID
    ) -> list[MaterialStockInfo]:
        """材料一覧を在庫レベル・使用可能日数付きで取得"""
        # 材料一覧を取得
        materials = await self.material_repo.find_by_category_id(category_id, user_id)

        # 各材料の使用可能日数を計算
        usage_days = await self.bulk_calculate_usage_days(user_id)

        # MaterialStockInfoに変換
        stock_infos = []
        for material in materials:
            daily_usage_rate = await self.calculate_material_usage_rate(
                material.id, 30, user_id
            )

            stock_info = MaterialStockInfo(
                material=material,
                stock_level=material.get_stock_level(),
                estimated_usage_days=usage_days.get(material.id),
                daily_usage_rate=Decimal(str(daily_usage_rate))
                if daily_usage_rate
                else None,
            )
            stock_infos.append(stock_info)

        return stock_infos

    async def calculate_material_usage_rate(
        self, material_id: UUID, days: int, user_id: UUID
    ) -> float | None:
        """材料の平均使用量を計算（日次）"""
        # 過去N日間の期間を設定
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 期間内の消費取引を取得（負の値のみ）
        transactions = (
            await self.stock_transaction_repo.find_by_material_and_date_range(
                material_id, start_date, end_date, user_id
            )
        )

        # 消費取引のみをフィルタ（負の値）
        consumption_transactions = [t for t in transactions if t.change_amount < 0]

        if not consumption_transactions:
            return None

        # 総消費量を計算（絶対値）
        total_consumption = sum(
            abs(float(t.change_amount)) for t in consumption_transactions
        )

        # 日次平均を計算
        return total_consumption / days if days > 0 else None

    async def calculate_estimated_usage_days(
        self, material_id: UUID, user_id: UUID
    ) -> int | None:
        """推定使用可能日数を計算"""
        # 材料を取得
        material = await self.material_repo.find_by_id(material_id)
        if not material or material.user_id != user_id:
            return None

        # 平均使用量を計算（過去30日間）
        daily_usage = await self.calculate_material_usage_rate(material_id, 30, user_id)

        if not daily_usage or daily_usage <= 0:
            return None

        # 現在在庫量 ÷ 日次使用量 = 使用可能日数
        estimated_days = float(material.current_stock) / daily_usage

        return int(estimated_days) if estimated_days >= 0 else 0

    async def bulk_calculate_usage_days(self, user_id: UUID) -> dict[UUID, int | None]:
        """全材料の使用可能日数を一括計算"""
        # 全材料を取得
        filters = {"user_id": (FilterOp.EQ, user_id)}
        materials = await self.material_repo.find(filters=filters)

        # 各材料の使用可能日数を計算
        usage_days = {}
        for material in materials:
            days = await self.calculate_estimated_usage_days(material.id, user_id)
            usage_days[material.id] = days

        return usage_days

    async def get_detailed_stock_alerts(
        self, user_id: UUID
    ) -> dict[str, list[MaterialStockInfo]]:
        """詳細な在庫アラート情報を取得（レベル別 + 詳細情報付き）"""
        # 全材料の在庫情報を取得
        all_materials_info = await self.get_materials_with_stock_info(None, user_id)

        # レベル別に分類
        alerts = {"critical": [], "low": [], "sufficient": []}

        for material_info in all_materials_info:
            if material_info.stock_level == StockLevel.CRITICAL:
                alerts["critical"].append(material_info)
            elif material_info.stock_level == StockLevel.LOW:
                alerts["low"].append(material_info)
            else:
                alerts["sufficient"].append(material_info)

        # 各レベル内で材料名でソート
        for level in alerts:
            alerts[level].sort(key=lambda x: x.material.name)

        return alerts

    async def consume_materials_for_order(self, order_id: UUID, user_id: UUID) -> bool:
        """注文に対する材料を消費（在庫減算）"""
        try:
            # 注文明細を取得
            order_items = await self.order_item_repo.find_by_order_id(order_id)

            if not order_items:
                return True  # 注文明細がない場合は成功とみなす

            # 注文明細から必要な材料を計算
            material_requirements = defaultdict(Decimal)

            for order_item in order_items:
                # メニューアイテムのレシピを取得
                recipes = await self.recipe_repo.find_by_menu_item_id(
                    order_item.menu_item_id, user_id
                )

                for recipe in recipes:
                    # 必要量 = レシピの必要量 × 注文数量
                    required_amount = recipe.required_amount * Decimal(
                        str(order_item.quantity)
                    )
                    material_requirements[recipe.material_id] += required_amount

            # 各材料の在庫を減算し、取引を記録
            transactions = []

            for material_id, required_amount in material_requirements.items():
                # 材料を取得
                material = await self.material_repo.find_by_id(material_id)
                if not material or material.user_id != user_id:
                    continue

                # 在庫を減算
                new_stock = material.current_stock - required_amount
                material.current_stock = max(
                    new_stock, Decimal("0")
                )  # 負の在庫は0にする

                # 材料を更新
                await self.material_repo.update(material.id, material)

                # 取引記録を作成（負の値で記録）
                transaction = StockTransaction(
                    material_id=material_id,
                    transaction_type=TransactionType.SALE,
                    change_amount=-required_amount,
                    reference_type=ReferenceType.ORDER,
                    reference_id=order_id,
                    notes=f"Order {order_id} consumption",
                    user_id=user_id,
                )
                transactions.append(transaction)

            # 取引を一括作成
            if transactions:
                await self.stock_transaction_repo.create_batch(transactions)

            return True

        except Exception:
            return False

    async def restore_materials_for_order(self, order_id: UUID, user_id: UUID) -> bool:
        """注文キャンセル時の材料を復元（在庫復旧）"""
        try:
            # 該当注文の消費取引を取得
            consumption_transactions = (
                await self.stock_transaction_repo.find_by_reference(
                    ReferenceType.ORDER.value, order_id, user_id
                )
            )

            # 消費取引（負の値）のみを対象
            consumption_only = [
                t
                for t in consumption_transactions
                if t.change_amount < 0 and t.transaction_type == TransactionType.SALE
            ]

            if not consumption_only:
                return True  # 消費取引がない場合は成功とみなす

            # 復元取引を作成
            restore_transactions = []

            for transaction in consumption_only:
                # 材料を取得
                material = await self.material_repo.find_by_id(transaction.material_id)
                if not material or material.user_id != user_id:
                    continue

                # 在庫を復元（消費量の絶対値を加算）
                restore_amount = abs(transaction.change_amount)
                material.current_stock += restore_amount

                # 材料を更新
                await self.material_repo.update(material.id, material)

                # 復元取引記録を作成（正の値で記録）
                restore_transaction = StockTransaction(
                    material_id=transaction.material_id,
                    transaction_type=TransactionType.ADJUSTMENT,
                    change_amount=restore_amount,
                    reference_type=ReferenceType.ORDER,
                    reference_id=order_id,
                    notes=f"Order {order_id} cancellation restore",
                    user_id=user_id,
                )
                restore_transactions.append(restore_transaction)

            # 復元取引を一括作成
            if restore_transactions:
                await self.stock_transaction_repo.create_batch(restore_transactions)

            return True

        except Exception:
            return False

    async def update_material_thresholds(
        self,
        material_id: UUID,
        alert_threshold: Decimal,
        critical_threshold: Decimal,
        user_id: UUID,
    ) -> Material:
        """材料のアラート閾値を更新"""
        # 材料を取得
        material = await self.material_repo.find_by_id(material_id)
        if not material or material.user_id != user_id:
            raise ValueError("Material not found or access denied")

        # 閾値の妥当性チェック
        if critical_threshold > alert_threshold:
            raise ValueError(
                "Critical threshold must be less than or equal to alert threshold"
            )

        if critical_threshold < 0 or alert_threshold < 0:
            raise ValueError("Thresholds must be non-negative")

        # 閾値を更新
        material.alert_threshold = alert_threshold
        material.critical_threshold = critical_threshold

        # 材料を更新して返す
        return await self.material_repo.update(material_id, material)
