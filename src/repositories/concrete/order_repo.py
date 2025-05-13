from typing import Any
from uuid import UUID

from models.order import Order, OrderItem
from repositories.abstruct.crud_repo import CrudRepository
from services.app_services.client_service import SupabaseClient


class OrderRepository(CrudRepository[Order]):
    def __init__(self, client: SupabaseClient) -> None:
        super().__init__(client, Order.__table_name__(), Order)

    async def get_orders_by_filter(self, query: Any) -> list[Order]:
        return await self.list(query)

    async def get_by_id(self, order_id: UUID) -> Order | None:
        return await self.read(str(order_id))

    # complete_orderはOrderServiceに移動したため削除

    async def update_order_items(
        self, order_id: UUID, items: list[OrderItem], *, returning: bool = True
    ) -> Order | None:
        return await self.upsert(str(order_id), {"items": items}, returning=returning)

    async def delete_order(self, order_id: UUID) -> bool:
        return await self.delete(str(order_id))


class OrderItemRepository(CrudRepository[OrderItem]):
    def __init__(self, client: SupabaseClient) -> None:
        super().__init__(client, OrderItem.__table_name__(), OrderItem)
