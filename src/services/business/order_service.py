from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from constants.options import FilterOp, PaymentMethod
from constants.status import OrderStatus
from models.domains.order import Order, OrderItem
from models.dto.order import (
    CartItemRequest,
    OrderCalculationResult,
    OrderCheckoutRequest,
    OrderSearchRequest,
)
from repositories.domains.inventory_repo import MaterialRepository, RecipeRepository
from repositories.domains.menu_repo import MenuItemRepository
from repositories.domains.order_repo import OrderItemRepository, OrderRepository
from services.platform.client_service import SupabaseClient
from utils.errors import NotFoundError, ValidationError


class CartService:
    """カート（下書き注文）管理サービス"""

    def __init__(self, client: SupabaseClient):
        self.order_repo = OrderRepository(client)
        self.order_item_repo = OrderItemRepository(client)
        self.menu_item_repo = MenuItemRepository(client)
        self.material_repo = MaterialRepository(client)
        self.recipe_repo = RecipeRepository(client)

    async def get_or_create_active_cart(self, user_id: UUID) -> Order:
        """アクティブなカート（下書き注文）を取得または作成"""
        # 既存のアクティブカートを検索
        existing_cart = await self.order_repo.find_active_draft_by_user(user_id)

        if existing_cart:
            return existing_cart

        # 新しいカートを作成
        new_cart = Order(
            total_amount=0,
            status=OrderStatus.PREPARING,
            payment_method=PaymentMethod.CASH,  # デフォルト値
            ordered_at=datetime.now(),
            user_id=user_id,
        )

        created_cart = await self.order_repo.create(new_cart)
        return created_cart

    async def add_item_to_cart(
        self, cart_id: UUID, request: CartItemRequest, user_id: UUID
    ) -> tuple[OrderItem, bool]:
        """カートに商品を追加（戻り値: (OrderItem, 在庫充足フラグ)）"""
        # カートの存在確認
        cart = await self.order_repo.find_by_id(cart_id)
        if not cart or cart.user_id != user_id:
            raise NotFoundError(f"Cart {cart_id} not found or access denied")

        # メニューアイテムの取得
        menu_item = await self.menu_item_repo.find_by_id(request.menu_item_id)
        if not menu_item or menu_item.user_id != user_id:
            raise NotFoundError(f"Menu item {request.menu_item_id} not found")

        # 在庫確認
        is_stock_sufficient = await self._check_menu_item_stock(
            request.menu_item_id, request.quantity, user_id
        )

        # 既存のアイテムがあるかチェック
        existing_item = await self.order_item_repo.find_existing_item(
            cart_id, request.menu_item_id
        )

        if existing_item:
            # 既存アイテムの数量を更新
            new_quantity = existing_item.quantity + request.quantity
            updated_item = await self.order_item_repo.update(
                existing_item.id,
                {
                    "quantity": new_quantity,
                    "subtotal": menu_item.price * new_quantity,
                    "selected_options": request.selected_options,
                    "special_request": request.special_request,
                },
            )

            # カート合計を更新
            await self._update_cart_total(cart_id)

            return updated_item, is_stock_sufficient
        else:
            # 新しいアイテムを作成
            order_item = OrderItem(
                order_id=cart_id,
                menu_item_id=request.menu_item_id,
                quantity=request.quantity,
                unit_price=menu_item.price,
                subtotal=menu_item.price * request.quantity,
                selected_options=request.selected_options,
                special_request=request.special_request,
                created_at=datetime.now(),
                user_id=user_id,
            )

            created_item = await self.order_item_repo.create(order_item)

            # カート合計を更新
            await self._update_cart_total(cart_id)

            return created_item, is_stock_sufficient

    async def update_cart_item_quantity(
        self, cart_id: UUID, order_item_id: UUID, new_quantity: int, user_id: UUID
    ) -> tuple[OrderItem, bool]:
        """カート内商品の数量を更新"""
        if new_quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")

        # カートと注文アイテムの存在確認
        cart = await self.order_repo.find_by_id(cart_id)
        if not cart or cart.user_id != user_id:
            raise NotFoundError(f"Cart {cart_id} not found or access denied")

        order_item = await self.order_item_repo.find_by_id(order_item_id)
        if not order_item or order_item.order_id != cart_id:
            raise NotFoundError(f"Order item {order_item_id} not found in cart")

        # メニューアイテムの取得（価格情報のため）
        menu_item = await self.menu_item_repo.find_by_id(order_item.menu_item_id)
        if not menu_item:
            raise NotFoundError(f"Menu item {order_item.menu_item_id} not found")

        # 在庫確認
        is_stock_sufficient = await self._check_menu_item_stock(
            order_item.menu_item_id, new_quantity, user_id
        )

        # 数量と小計を更新
        updated_item = await self.order_item_repo.update(
            order_item_id,
            {"quantity": new_quantity, "subtotal": menu_item.price * new_quantity},
        )

        # カート合計を更新
        await self._update_cart_total(cart_id)

        return updated_item, is_stock_sufficient

    async def remove_item_from_cart(
        self, cart_id: UUID, order_item_id: UUID, user_id: UUID
    ) -> bool:
        """カートから商品を削除"""
        # カートの存在確認
        cart = await self.order_repo.find_by_id(cart_id)
        if not cart or cart.user_id != user_id:
            raise NotFoundError(f"Cart {cart_id} not found or access denied")

        # 注文アイテムの存在確認
        order_item = await self.order_item_repo.find_by_id(order_item_id)
        if not order_item or order_item.order_id != cart_id:
            raise NotFoundError(f"Order item {order_item_id} not found in cart")

        # アイテムを削除
        success = await self.order_item_repo.delete(order_item_id)

        if success:
            # カート合計を更新
            await self._update_cart_total(cart_id)

        return success

    async def clear_cart(self, cart_id: UUID, user_id: UUID) -> bool:
        """カートを空にする"""
        # カートの存在確認
        cart = await self.order_repo.find_by_id(cart_id)
        if not cart or cart.user_id != user_id:
            raise NotFoundError(f"Cart {cart_id} not found or access denied")

        # カート内の全アイテムを削除
        success = await self.order_item_repo.delete_by_order_id(cart_id)

        if success:
            # カートの合計金額をリセット
            await self.order_repo.update(cart_id, {"total_amount": 0})

        return success

    async def calculate_cart_total(
        self, cart_id: UUID, discount_amount: int = 0
    ) -> OrderCalculationResult:
        """カートの金額を計算"""
        # カート内のアイテムを取得
        cart_items = await self.order_item_repo.find_by_order_id(cart_id)

        # 小計の計算
        subtotal = sum(item.subtotal for item in cart_items)

        # 税率（8%と仮定）
        tax_rate = 0.08
        tax_amount = int(subtotal * tax_rate)

        # 合計金額の計算
        total_amount = subtotal + tax_amount - discount_amount

        return OrderCalculationResult(
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=max(0, total_amount),  # マイナスにならないように
        )

    async def validate_cart_stock(
        self, cart_id: UUID, user_id: UUID
    ) -> dict[UUID, bool]:
        """カート内全商品の在庫を検証（戻り値: {order_item_id: 在庫充足フラグ}）"""
        # カートの存在確認
        cart = await self.order_repo.find_by_id(cart_id)
        if not cart or cart.user_id != user_id:
            raise NotFoundError(f"Cart {cart_id} not found or access denied")

        # カート内のアイテムを取得
        cart_items = await self.order_item_repo.find_by_order_id(cart_id)

        stock_validation = {}

        for item in cart_items:
            is_sufficient = await self._check_menu_item_stock(
                item.menu_item_id, item.quantity, user_id
            )
            stock_validation[item.id] = is_sufficient

        return stock_validation


class OrderService:
    """注文管理サービス"""

    def __init__(self, client: SupabaseClient):
        self.order_repo = OrderRepository(client)
        self.order_item_repo = OrderItemRepository(client)
        self.menu_item_repo = MenuItemRepository(client)
        self.material_repo = MaterialRepository(client)
        self.recipe_repo = RecipeRepository(client)

    async def checkout_cart(
        self, cart_id: UUID, request: OrderCheckoutRequest, user_id: UUID
    ) -> tuple[Order, bool]:
        """カートを確定して正式注文に変換（戻り値: (Order, 成功フラグ)）"""
        # カートの存在確認
        cart = await self.order_repo.find_by_id(cart_id)
        if not cart or cart.user_id != user_id:
            raise NotFoundError(f"Cart {cart_id} not found or access denied")

        if cart.status != OrderStatus.PREPARING:
            raise ValidationError("Cart is not in preparing status")

        # カート内アイテムの取得
        cart_items = await self.order_item_repo.find_by_order_id(cart_id)
        if not cart_items:
            raise ValidationError("Cart is empty")

        # 在庫確認
        stock_validation = {}
        all_sufficient = True

        for item in cart_items:
            is_sufficient = await self._check_menu_item_stock(
                item.menu_item_id, item.quantity, user_id
            )
            stock_validation[item.id] = is_sufficient
            if not is_sufficient:
                all_sufficient = False

        if not all_sufficient:
            return cart, False

        # 材料消費の実行
        await self._consume_materials_for_order(cart_items, user_id)

        # 注文の確定
        # Note: Order number generation for future use
        await self.order_repo.generate_next_order_number(user_id)

        updated_order = await self.order_repo.update(
            cart_id,
            {
                "payment_method": request.payment_method,
                "customer_name": request.customer_name,
                "discount_amount": request.discount_amount,
                "notes": request.notes,
                "ordered_at": datetime.now(),
                "status": OrderStatus.PREPARING,
            },
        )

        # 最終金額を計算して更新
        calculation = await self._calculate_order_total(
            cart_id, request.discount_amount
        )
        await self.order_repo.update(
            cart_id, {"total_amount": calculation.total_amount}
        )

        return updated_order, True

    async def cancel_order(
        self, order_id: UUID, reason: str, user_id: UUID
    ) -> tuple[Order, bool]:
        """注文をキャンセル（在庫復元含む）"""
        # 注文の存在確認
        order = await self.order_repo.find_by_id(order_id)
        if not order or order.user_id != user_id:
            raise NotFoundError(f"Order {order_id} not found or access denied")

        if order.status == OrderStatus.CANCELED:
            return order, False  # 既にキャンセル済み

        if order.status == OrderStatus.COMPLETED:
            raise ValidationError("Cannot cancel completed order")

        # 材料在庫を復元（まだ調理開始前の場合のみ）
        if not order.started_preparing_at:
            order_items = await self.order_item_repo.find_by_order_id(order_id)
            await self._restore_materials_from_order(order_items, user_id)

        # 注文をキャンセル状態に更新
        canceled_order = await self.order_repo.update(
            order_id,
            {
                "status": OrderStatus.CANCELED,
                "notes": f"{order.notes or ''} [CANCELED: {reason}]".strip(),
            },
        )

        return canceled_order, True

    async def get_order_history(
        self, request: OrderSearchRequest, user_id: UUID
    ) -> dict[str, Any]:
        """注文履歴を取得（ページネーション付き）"""
        # フィルタの構築
        filters = {"user_id": (FilterOp.EQ, user_id)}

        if request.status_filter:
            filters["status"] = (FilterOp.IN, request.status_filter)

        if request.customer_name:
            filters["customer_name"] = (FilterOp.ILIKE, f"%{request.customer_name}%")

        # 日付範囲での検索
        if request.date_from and request.date_to:
            orders, total_count = await self.order_repo.search_with_pagination(
                filters, request.page, request.limit
            )
            # 手動で日付フィルタリング（リポジトリでサポートされていない場合）
            if request.date_from or request.date_to:
                date_filtered_orders = []
                for order in orders:
                    if request.date_from and order.ordered_at < request.date_from:
                        continue
                    if request.date_to and order.ordered_at > request.date_to:
                        continue
                    date_filtered_orders.append(order)
                orders = date_filtered_orders
        else:
            orders, total_count = await self.order_repo.search_with_pagination(
                filters, request.page, request.limit
            )

        # メニューアイテム名での検索（必要に応じて）
        if request.menu_item_name:
            filtered_orders = []
            for order in orders:
                items = await self.order_item_repo.find_by_order_id(order.id)
                for item in items:
                    menu_item = await self.menu_item_repo.find_by_id(item.menu_item_id)
                    if (
                        menu_item
                        and request.menu_item_name.lower() in menu_item.name.lower()
                    ):
                        filtered_orders.append(order)
                        break
            orders = filtered_orders

        return {
            "orders": orders,
            "total_count": total_count,
            "page": request.page,
            "limit": request.limit,
            "total_pages": (total_count + request.limit - 1) // request.limit,
        }

    async def get_order_details(self, order_id: UUID, user_id: UUID) -> Order | None:
        """注文詳細を取得"""
        order = await self.order_repo.find_by_id(order_id)
        if not order or order.user_id != user_id:
            return None
        return order

    async def get_order_with_items(
        self, order_id: UUID, user_id: UUID
    ) -> dict[str, Any] | None:
        """注文と注文明細を一括取得"""
        order = await self.get_order_details(order_id, user_id)
        if not order:
            return None

        order_items = await self.order_item_repo.find_by_order_id(order_id)

        # メニューアイテム情報も含める
        items_with_menu = []
        for item in order_items:
            menu_item = await self.menu_item_repo.find_by_id(item.menu_item_id)
            items_with_menu.append({"order_item": item, "menu_item": menu_item})

        return {
            "order": order,
            "items": items_with_menu,
            "total_items": len(order_items),
        }


class KitchenService:
    """調理・キッチン管理サービス"""

    def __init__(self, client: SupabaseClient):
        self.order_repo = OrderRepository(client)
        self.order_item_repo = OrderItemRepository(client)
        self.menu_item_repo = MenuItemRepository(client)
        self.material_repo = MaterialRepository(client)
        self.recipe_repo = RecipeRepository(client)

    async def get_active_orders_by_status(
        self, user_id: UUID
    ) -> dict[OrderStatus, list[Order]]:
        """ステータス別進行中注文を取得"""
        active_statuses = [OrderStatus.PREPARING]
        active_orders = await self.order_repo.find_by_status_list(
            active_statuses, user_id
        )

        # ステータス別に分類
        orders_by_status = defaultdict(list)
        for order in active_orders:
            orders_by_status[order.status].append(order)

        return dict(orders_by_status)

    async def get_order_queue(self, user_id: UUID) -> list[Order]:
        """注文キューを取得（調理順序順）"""
        active_orders = await self.order_repo.find_by_status_list(
            [OrderStatus.PREPARING], user_id
        )

        # 調理開始前の注文を優先順位順に並べる
        not_started = [o for o in active_orders if not o.started_preparing_at]
        in_progress = [
            o for o in active_orders if o.started_preparing_at and not o.ready_at
        ]

        # 注文時刻順に並べる
        not_started.sort(key=lambda x: x.ordered_at)
        in_progress.sort(key=lambda x: x.started_preparing_at or x.ordered_at)

        return not_started + in_progress

    async def start_order_preparation(self, order_id: UUID, user_id: UUID) -> Order:
        """注文の調理を開始"""
        order = await self.order_repo.find_by_id(order_id)
        if not order or order.user_id != user_id:
            raise NotFoundError(f"Order {order_id} not found or access denied")

        if order.status != OrderStatus.PREPARING:
            raise ValidationError("Order is not in preparing status")

        if order.started_preparing_at:
            raise ValidationError("Order preparation already started")

        # 調理開始時刻を記録
        updated_order = await self.order_repo.update(
            order_id, {"started_preparing_at": datetime.now()}
        )

        return updated_order

    async def complete_order_preparation(self, order_id: UUID, user_id: UUID) -> Order:
        """注文の調理を完了"""
        order = await self.order_repo.find_by_id(order_id)
        if not order or order.user_id != user_id:
            raise NotFoundError(f"Order {order_id} not found or access denied")

        if not order.started_preparing_at:
            raise ValidationError("Order preparation not started")

        if order.ready_at:
            raise ValidationError("Order already completed")

        # 調理完了時刻を記録
        updated_order = await self.order_repo.update(
            order_id, {"ready_at": datetime.now()}
        )

        return updated_order

    async def mark_order_ready(self, order_id: UUID, user_id: UUID) -> Order:
        """注文を提供準備完了にマーク"""
        # complete_order_preparationと同じ処理
        return await self.complete_order_preparation(order_id, user_id)

    async def deliver_order(self, order_id: UUID, user_id: UUID) -> Order:
        """注文を提供完了"""
        order = await self.order_repo.find_by_id(order_id)
        if not order or order.user_id != user_id:
            raise NotFoundError(f"Order {order_id} not found or access denied")

        if not order.ready_at:
            raise ValidationError("Order not ready for delivery")

        if order.status == OrderStatus.COMPLETED:
            raise ValidationError("Order already delivered")

        # 提供完了
        updated_order = await self.order_repo.update(
            order_id, {"status": OrderStatus.COMPLETED, "completed_at": datetime.now()}
        )

        return updated_order

    async def calculate_estimated_completion_time(
        self, order_id: UUID, user_id: UUID
    ) -> datetime | None:
        """完成予定時刻を計算"""
        order = await self.order_repo.find_by_id(order_id)
        if not order or order.user_id != user_id:
            return None

        if order.status == OrderStatus.COMPLETED:
            return order.completed_at

        # 注文アイテムの調理時間を計算
        order_items = await self.order_item_repo.find_by_order_id(order_id)
        total_prep_time = 0

        for item in order_items:
            menu_item = await self.menu_item_repo.find_by_id(item.menu_item_id)
            if menu_item:
                total_prep_time += menu_item.estimated_prep_time_minutes * item.quantity

        # 基準時刻（調理開始時刻または注文時刻）
        base_time = order.started_preparing_at or order.ordered_at

        # キューでの待ち時間を考慮
        if not order.started_preparing_at:
            queue_wait_time = await self.calculate_queue_wait_time(user_id)
            total_prep_time += queue_wait_time

        return base_time + timedelta(minutes=total_prep_time)

    async def adjust_estimated_completion_time(
        self, order_id: UUID, additional_minutes: int, user_id: UUID
    ) -> Order:
        """完成予定時刻を調整"""
        order = await self.order_repo.find_by_id(order_id)
        if not order or order.user_id != user_id:
            raise NotFoundError(f"Order {order_id} not found or access denied")

        # ノート欄に調整理由を記録
        adjustment_note = f"Est. time adjusted by {additional_minutes} minutes"
        current_notes = order.notes or ""
        new_notes = f"{current_notes} [{adjustment_note}]".strip()

        updated_order = await self.order_repo.update(order_id, {"notes": new_notes})

        return updated_order

    async def update_kitchen_status(
        self, active_staff_count: int, notes: str | None, user_id: UUID
    ) -> bool:
        """キッチン状況を更新"""
        # キッチン状況は別のモデルで管理されることを想定
        # ここでは簡単にログして成功を返す（実装は要件に応じて）
        print(
            f"Kitchen status updated for user {user_id}: {active_staff_count} staff, notes: {notes}"
        )
        return True

    async def get_kitchen_workload(self, user_id: UUID) -> dict[str, Any]:
        """キッチンの負荷状況を取得"""
        active_orders = await self.order_repo.find_by_status_list(
            [OrderStatus.PREPARING], user_id
        )

        not_started_count = len(
            [o for o in active_orders if not o.started_preparing_at]
        )
        in_progress_count = len(
            [o for o in active_orders if o.started_preparing_at and not o.ready_at]
        )
        ready_count = len(
            [
                o
                for o in active_orders
                if o.ready_at and o.status != OrderStatus.COMPLETED
            ]
        )

        # 推定総調理時間を計算
        total_estimated_minutes = 0
        for order in active_orders:
            if not order.ready_at:  # まだ完成していない注文
                order_items = await self.order_item_repo.find_by_order_id(order.id)
                for item in order_items:
                    menu_item = await self.menu_item_repo.find_by_id(item.menu_item_id)
                    if menu_item:
                        total_estimated_minutes += (
                            menu_item.estimated_prep_time_minutes * item.quantity
                        )

        return {
            "total_active_orders": len(active_orders),
            "not_started_count": not_started_count,
            "in_progress_count": in_progress_count,
            "ready_count": ready_count,
            "estimated_total_minutes": total_estimated_minutes,
            "average_wait_time_minutes": await self.calculate_queue_wait_time(user_id),
        }

    async def calculate_queue_wait_time(self, user_id: UUID) -> int:
        """注文キューの待ち時間を計算（分）"""
        queue = await self.get_order_queue(user_id)

        total_wait_time = 0
        for order in queue:
            if not order.started_preparing_at:  # まだ開始していない注文
                order_items = await self.order_item_repo.find_by_order_id(order.id)
                for item in order_items:
                    menu_item = await self.menu_item_repo.find_by_id(item.menu_item_id)
                    if menu_item:
                        total_wait_time += (
                            menu_item.estimated_prep_time_minutes * item.quantity
                        )

        # 簡単な計算（実際はより複雑な計算が必要）
        return total_wait_time // max(1, len(queue))

    async def optimize_cooking_order(self, user_id: UUID) -> list[UUID]:
        """調理順序を最適化（注文IDリストを返す）"""
        not_started_orders = await self.order_repo.find_by_status_list(
            [OrderStatus.PREPARING], user_id
        )
        not_started_orders = [
            o for o in not_started_orders if not o.started_preparing_at
        ]

        # 最適化アルゴリズム（簡単な例：調理時間の短い順）
        order_prep_times = []

        for order in not_started_orders:
            order_items = await self.order_item_repo.find_by_order_id(order.id)
            total_time = 0
            for item in order_items:
                menu_item = await self.menu_item_repo.find_by_id(item.menu_item_id)
                if menu_item:
                    total_time += menu_item.estimated_prep_time_minutes * item.quantity

            order_prep_times.append((order.id, total_time, order.ordered_at))

        # 調理時間の短い順、同じ時間なら注文の早い順
        order_prep_times.sort(key=lambda x: (x[1], x[2]))

        return [order_id for order_id, _, _ in order_prep_times]

    async def predict_completion_times(self, user_id: UUID) -> dict[UUID, datetime]:
        """全注文の完成予定時刻を予測"""
        active_orders = await self.order_repo.find_by_status_list(
            [OrderStatus.PREPARING], user_id
        )
        completion_times = {}

        for order in active_orders:
            estimated_time = await self.calculate_estimated_completion_time(
                order.id, user_id
            )
            if estimated_time:
                completion_times[order.id] = estimated_time

        return completion_times

    async def get_kitchen_performance_metrics(
        self, target_date: datetime, user_id: UUID
    ) -> dict[str, Any]:
        """キッチンパフォーマンス指標を取得"""
        # 指定日の完了注文を取得
        completed_orders = await self.order_repo.find_completed_by_date(
            target_date, user_id
        )

        if not completed_orders:
            return {
                "total_orders": 0,
                "average_prep_time_minutes": 0,
                "total_revenue": 0,
                "fastest_order_minutes": 0,
                "slowest_order_minutes": 0,
            }

        # 調理時間の分析
        prep_times = []
        total_revenue = 0

        for order in completed_orders:
            prep_time = self.get_actual_prep_time_minutes(order)
            if prep_time is not None:
                prep_times.append(prep_time)

            total_revenue += order.total_amount

        if prep_times:
            average_prep_time = sum(prep_times) / len(prep_times)
            fastest_order = min(prep_times)
            slowest_order = max(prep_times)
        else:
            average_prep_time = 0
            fastest_order = 0
            slowest_order = 0

        return {
            "total_orders": len(completed_orders),
            "average_prep_time_minutes": round(average_prep_time, 1),
            "total_revenue": total_revenue,
            "fastest_order_minutes": round(fastest_order, 1),
            "slowest_order_minutes": round(slowest_order, 1),
            "orders_per_hour": len(completed_orders) / 24 if completed_orders else 0,
        }

    def get_actual_prep_time_minutes(self, order: Order) -> int | None:
        """実際の調理時間を取得（分）"""
        if order.started_preparing_at and order.ready_at:
            delta = order.ready_at - order.started_preparing_at
            return int(delta.total_seconds() / 60)
        return None

    # Helper methods for all services
    async def _check_menu_item_stock(
        self, menu_item_id: UUID, quantity: int, user_id: UUID
    ) -> bool:
        """メニューアイテムの在庫充足を確認"""
        # レシピを取得
        recipes = await self.recipe_repo.find_by_menu_item_id(menu_item_id, user_id)

        for recipe in recipes:
            if recipe.is_optional:
                continue

            # 必要な材料量を計算
            required_amount = recipe.required_amount * quantity

            # 材料の在庫を確認
            material = await self.material_repo.find_by_id(recipe.material_id)
            if not material or material.current_stock < required_amount:
                return False

        return True

    async def _update_cart_total(self, cart_id: UUID) -> None:
        """カートの合計金額を更新"""
        cart_items = await self.order_item_repo.find_by_order_id(cart_id)
        total_amount = sum(item.subtotal for item in cart_items)
        await self.order_repo.update(cart_id, {"total_amount": total_amount})

    async def _calculate_order_total(
        self, order_id: UUID, discount_amount: int = 0
    ) -> OrderCalculationResult:
        """注文の金額を計算"""
        order_items = await self.order_item_repo.find_by_order_id(order_id)

        subtotal = sum(item.subtotal for item in order_items)
        tax_rate = 0.08
        tax_amount = int(subtotal * tax_rate)
        total_amount = subtotal + tax_amount - discount_amount

        return OrderCalculationResult(
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=max(0, total_amount),
        )

    async def _consume_materials_for_order(
        self, order_items: list[OrderItem], user_id: UUID
    ) -> None:
        """注文に対する材料消費を実行"""
        material_consumption = defaultdict(Decimal)

        # 必要な材料量を集計
        for item in order_items:
            recipes = await self.recipe_repo.find_by_menu_item_id(
                item.menu_item_id, user_id
            )
            for recipe in recipes:
                if not recipe.is_optional:
                    required_amount = recipe.required_amount * item.quantity
                    material_consumption[recipe.material_id] += required_amount

        # 材料在庫を消費
        for material_id, consumed_amount in material_consumption.items():
            material = await self.material_repo.find_by_id(material_id)
            if material:
                new_stock = material.current_stock - consumed_amount
                await self.material_repo.update_stock_amount(
                    material_id, new_stock, user_id
                )

    async def _restore_materials_from_order(
        self, order_items: list[OrderItem], user_id: UUID
    ) -> None:
        """注文キャンセル時の材料在庫復元"""
        material_restoration = defaultdict(Decimal)

        # 復元する材料量を集計
        for item in order_items:
            recipes = await self.recipe_repo.find_by_menu_item_id(
                item.menu_item_id, user_id
            )
            for recipe in recipes:
                if not recipe.is_optional:
                    restored_amount = recipe.required_amount * item.quantity
                    material_restoration[recipe.material_id] += restored_amount

        # 材料在庫を復元
        for material_id, restored_amount in material_restoration.items():
            material = await self.material_repo.find_by_id(material_id)
            if material:
                new_stock = material.current_stock + restored_amount
                await self.material_repo.update_stock_amount(
                    material_id, new_stock, user_id
                )
