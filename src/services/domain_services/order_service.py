from decimal import Decimal

from constants.order_status import OrderStatus
from models.order import Order, OrderItem
from repositories.concrete.inventory_item_repo import InventoryItemRepository
from repositories.concrete.order_repo import OrderItemRepository, OrderRepository


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

    # TODO: 続き書く。Obsidianのusecase_process_flowに書いた内容を参考にする

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
