from decimal import Decimal

from constants.order_status import OrderStatus
from models.order import Order, OrderItem
from repositories.concrete.inventory_item_repo import InventoryItemRepository
from repositories.concrete.order_repo import OrderItemRepository, OrderRepository
from utils.query_utils import QueryFilterUtils


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        order_item_repo: OrderItemRepository,
        inv_item_repo: InventoryItemRepository,
    ) -> None:
        self.order_repo = order_repo
        self.order_item_repo = order_item_repo
        self.inv_item_repo = inv_item_repo

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

        # 1. 関係していた、Order、InventoryItemを取得
        order = await self.order_repo.get_by_id(order_id)
        base_query = self.order_item_repo._get_base_query()
        order_item_query = QueryFilterUtils().filter_eq(
            base_query, "order_id", order_id
        )
        order_items = await self.order_item_repo.list(order_item_query)

        if not order:
            raise ValueError("注文が見つかりません")
        if not inventory_items:
            raise ValueError("在庫アイテムが見つかりません")

        # 2. Orderのitemsを更新(itemsを新しいものに置き換え)
        order.items = items

        # 3. 取得したInventoryItemのstockを、OrderItemのquantity分だけ増減させて保持しておく

        return

    async def calculate_total(self, items: list[OrderItem]) -> Decimal:
        if not items:
            return Decimal(0)
        elif 0 in [item.quantity for item in items]:
            raise ValueError("数量が0のアイテムがあります")

        # itemsからinventory_item_idを取得
        item_ids = [item.inventory_item_id for item in items]

        # inventory_item_idを元に、inventory_itemsを取得
        inventory_items = await self.inv_item_repo.bulk_get(item_ids)

        # inventory_itemsとitemsをzipして、合計金額を計算
        total: Decimal = sum(
            Decimal(item.price) * Decimal(order_item.quantity)
            for item, order_item in zip(inventory_items, items)
        )
        return total
