from typing import Any
from uuid import UUID

from models.order import Order, OrderItem
from repositories.abstruct.crud_repo import CrudRepository
from services.app_services.client_service import SupabaseClient
from utils.query_utils import QueryFilterUtils


class OrderRepository(CrudRepository[Order]):
    def __init__(self, client: SupabaseClient) -> None:
        super().__init__(client, Order.__table_name__(), Order)

    async def get_orders_by_filter(self, query: Any) -> list[Order]:
        return await self.list_entities(query)

    async def get_by_id(self, order_id: UUID) -> Order | None:
        return await self.read(str(order_id))

    async def update_order_items(
        self, order_id: UUID, items: list[OrderItem], *, returning: bool = True
    ) -> Order | None:
        dumped_items = [self._dump(item) for item in items]
        return await self.update(
            str(order_id), {"items": dumped_items}, returning=returning
        )

    async def delete_order(self, order_id: UUID) -> bool:
        return await self.delete(str(order_id))


class OrderItemRepository(CrudRepository[OrderItem]):
    def __init__(self, client: SupabaseClient) -> None:
        super().__init__(client, OrderItem.__table_name__(), OrderItem)

    async def get_order_items_by_order_id(
        self, order_id: UUID
    ) -> list[OrderItem] | None:
        query = QueryFilterUtils().filter_equal(
            self._base_query, "order_id", str(order_id)
        )
        return await self.list_entities(query)

    async def update_order_items(
        self, order_id: UUID, items: list[OrderItem], *, returning: bool = True
    ) -> Order | None:
        dumped_items = [self._dump(item) for item in items]
        return await self.update(
            str(order_id), {"items": dumped_items}, returning=returning
        )
