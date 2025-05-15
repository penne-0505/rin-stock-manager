from datetime import datetime
from decimal import Decimal
from uuid import UUID

from constants.order_status import OrderStatus
from constants.timezone import DefaultTZ
from constants.transaction_mode import TransactionMode
from models.order import Order, OrderItem
from repositories.concrete.inventory_item_repo import InventoryItemRepository
from repositories.concrete.order_repo import OrderItemRepository, OrderRepository
from repositories.concrete.transaction_repo import InventoryTransactionRepository
from utils.query_utils import QueryFilterUtils


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        order_item_repo: OrderItemRepository,
        inv_item_repo: InventoryItemRepository,
        inv_transaction_repo: InventoryTransactionRepository,
    ) -> None:
        self.order_repo = order_repo
        self.order_item_repo = order_item_repo
        self.inv_item_repo = inv_item_repo
        self.inv_transaction_repo = inv_transaction_repo

    async def create_order(
        self,
        items: list[OrderItem],
    ) -> Order:
        if not items:
            raise ValueError("アイテムがありません")

        total = await self.calculate_total(items)

        order = Order(
            items=items,
            total=total,
            status=OrderStatus.PREPARING,
        )

        await self.order_repo.create(order)

    async def update_order(
        self,
        order_id: str,
        items: list[OrderItem],
    ) -> Order:
        """
        注文、それに関連するアイテム群をリセット ->
        1. 関係していた、Order、InventoryItemを取得
        2. Orderのitemsを更新(itemsを新しいものに置き換え)
        3. 取得したInventoryItemのstockを、OrderItemのquantity分だけ増減させて保持しておく
        4. 関係するInventoryTransactionを削除
        5. 更新後のOrder,InventoryItemから、InventoryTransactionを作成
        7. Orderのtotalを計算して保持
        8. 保持していたInventoryItemのstockを更新
        9. Orderのitems,totalを更新
        10. Orderを返す
        (終了)

        Order取得、紐づけられたOrderItem取得のためのクエリ作成、listでOrderItem取得、OrderItemからInventoryItemのIDを取得、
        InventoryItemのIDを元にInventoryItemを取得するためのクエリ作成、InventoryItem取得、InventoryItemのstockを更新、

        Orderのitemsを更新、totalを再計算、各InventoryItemに対してInventoryTransactionを作成、Orderをreturn
        """

        # !リポジトリアクセスにawaitを使用していないのは、Supabaseのクライアントが非同期であるため

        # order_idを元にOrderItemsを取得
        related_order_items = items

        # InventoryItemのIDを取得
        inv_item_ids = [item.inventory_item_id for item in related_order_items]
        # InventoryItemのIDを元にInventoryItemを取得するためのクエリ作成
        base_query = self.inv_item_repo._get_base_query()
        item_ids_query = QueryFilterUtils().filter_in(base_query, "id", inv_item_ids)
        # InventoryItemのIDを元にInventoryItemを取得
        related_inventory_items = self.inv_item_repo.list_entities(item_ids_query)

        # 関連するInventoryTransactionを取得
        # TODO: 関連トランザクション取得 -> 関連するトランザクションを削除 -> InventoryItem,OrderItemの更新終了後にTransactionを作成 -> Order返却
        related_inv_transactions = self.inv_transaction_repo.get_by_item_ids(
            inv_item_ids
        )
        transaction_ids = [transaction.id for transaction in related_inv_transactions]
        # 関連するInventoryTransactionを削除
        self.inv_transaction_repo.bulk_delete(transaction_ids)

        # InventoryItemのstockを更新
        for item in related_inventory_items:
            order_item = next(
                (oi for oi in related_order_items if oi.inventory_item_id == item.id),
                None,
            )
            if order_item:
                item.stock -= order_item.quantity

        # Orderのitemsを更新
        updated_order = self.order_item_repo.update_order_items(
            UUID(order_id), related_order_items, returning=True
        )

        updated_order_items = [order.items for order in updated_order]

        # Orderのtotalを再計算
        order_total = self.calculate_total(updated_order_items)

        # 各InventoryItemに対してInventoryTransactionを作成
        for item in related_inventory_items:
            order_item = next(
                (oi for oi in related_order_items if oi.inventory_item_id == item.id),
                None,
            )
            if order_item:
                transaction = {
                    "item_id": item.id,
                    "change": -order_item.quantity,
                    "type": TransactionMode.SALE,
                }
                self.inv_transaction_repo.create(transaction)

        # TODO: ちょっといろいろおかしい。orderをupdateするのにあたって、「何をするべきか」再考して実装しなおす。

        return

    async def calculate_total(self, items: list[OrderItem]) -> Decimal:
        if not items:
            return Decimal(0)
        elif 0 in [item.quantity for item in items]:
            raise ValueError("数量が0のアイテムがあります")

        # itemsからinventory_item_idを取得
        item_ids = [item.inventory_item_id for item in items]

        # inventory_item_idを元に、inventory_itemsを取得
        base_query = self.inv_item_repo.self._base_query()
        item_query = QueryFilterUtils().filter_in(base_query, "id", item_ids)
        inventory_items = await self.inv_item_repo.list_entities(item_query)

        # inventory_itemsとitemsをzipして、合計金額を計算
        total: Decimal = sum(
            Decimal(item.price) * Decimal(order_item.quantity)
            for item, order_item in zip(inventory_items, items)
        )
        return total

    async def complete_order(
        self, order_id: str, *, returning: bool = True
    ) -> Order | None:
        """
        指定した注文を完了状態にし、completed_atを現在時刻で更新する
        """

        now = datetime.now(DefaultTZ)
        return await self.order_repo.upsert(
            order_id,
            {
                "status": OrderStatus.COMPLETED,
                "completed_at": now,
            },
            returning=returning,
        )
