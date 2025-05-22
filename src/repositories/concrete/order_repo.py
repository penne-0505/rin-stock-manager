from uuid import UUID

from models.order import Order, OrderItem
from services.client_service import SupabaseClient
from src.repositories.abstract.crud_repo import CrudRepository


class OrderRepository(CrudRepository[Order, UUID]):
    def __init__(self, client: SupabaseClient):
        super().__init__(client, Order)


class OrderItemRepository(CrudRepository[OrderItem, UUID]):
    def __init__(self, client: SupabaseClient):
        super().__init__(client, OrderItem)
