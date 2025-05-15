from uuid import UUID

from models.inventory import InventoryTransaction
from repositories.abstruct.crud_repo import CrudRepository
from services.app_services.client_service import SupabaseClient
from utils.query_utils import QueryFilterUtils


class InventoryTransactionRepository(CrudRepository[InventoryTransaction]):
    def __init__(self, client: SupabaseClient) -> None:
        super().__init__(
            client, InventoryTransaction.__table_name__(), InventoryTransaction
        )

    async def get_by_item_id(self, inv_item_id: UUID) -> InventoryTransaction | None:
        query = QueryFilterUtils().filter_equal(
            self._base_query, "item_id", str(inv_item_id)
        )
        return await self.list_entities(query)

    async def get_by_item_ids(
        self, inv_item_ids: list[UUID]
    ) -> list[InventoryTransaction] | None:
        query = QueryFilterUtils().filter_in(
            self._base_query, "item_id", [str(id) for id in inv_item_ids]
        )
        return await self.list_entities(query)

    async def delete_by_item_ids(self, inv_item_ids: list[UUID]) -> None:
        query = QueryFilterUtils().filter_in(
            self._base_query, "item_id", [str(id) for id in inv_item_ids]
        )
        await self.delete(query)
