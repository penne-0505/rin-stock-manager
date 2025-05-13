from datetime import datetime
from typing import Any

from constants.order_status import OrderStatus
from constants.timezone import DefaultTZ
from models.order import Order, OrderItem
from repositories.abstruct.crud_repo import CrudRepository
from services.app_services.client_service import SupabaseClient


class OrderRepository(CrudRepository[Order]):
    def __init__(self, client: SupabaseClient) -> None:
        super().__init__(client, Order.__table_name__(), Order)

    async def get_orders_by_filter(self, query: Any) -> list[Order]:
        return await self.list(query)

    async def get_by_id(self, order_id: str) -> Order | None:
        return await self.read(order_id)

    async def complete_order(
        self, order_id: str, *, returning: bool = True
    ) -> Order | None:
        now = datetime.now(DefaultTZ)
        return await self.upsert(
            order_id,
            {
                "status": OrderStatus.COMPLETED,
                "completed_at": now,
            },
            returning=returning,
        )

    async def update_order_items(
        self, order_id: str, items: list[OrderItem], *, returning: bool = True
    ) -> Order | None:
        return await self.upsert(order_id, {"items": items}, returning=returning)

    async def delete_order(self, order_id: str) -> bool:
        return await self.delete(order_id)


class OrderItemRepository(CrudRepository[OrderItem]):
    def __init__(self, client: SupabaseClient) -> None:
        super().__init__(client, OrderItem.__table_name__(), OrderItem)
