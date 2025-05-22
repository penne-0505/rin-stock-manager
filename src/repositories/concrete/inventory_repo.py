from uuid import UUID

from models.inventory import InventoryItem, InventoryTransaction
from services.client_service import SupabaseClient
from src.repositories.abstract.crud_repo import CrudRepository


class InvItemRepository(CrudRepository[InventoryItem, UUID]):
    def __init__(self, client: SupabaseClient):
        super().__init__(client, InventoryItem)


class InvTxRepository(CrudRepository[InventoryTransaction, UUID]):
    def __init__(self, client: SupabaseClient):
        super().__init__(client, InventoryTransaction)
