from datetime import datetime, timedelta, timezone
from uuid import UUID
from decimal import Decimal

from models.inventory import InventoryItem
from repositories.abstruct.crud_repo import CrudRepository
from services.app_services.client_service import SupabaseClient

class InventoryItemRepository(CrudRepository[InventoryItem]):
    def __init__(self, client: SupabaseClient) -> None:
        super().__init__(client, InventoryItem.__table_name__())
    
    def get