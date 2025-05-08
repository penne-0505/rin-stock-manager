from datetime import datetime

from pydantic import BaseModel


class SyncRecord(BaseModel):
    id: str
    record_type: str
    payload: dict
    synced: bool
    timestamp: datetime
    user_id: str

    def __table_name__(cls) -> str:
        return "sync_records"
