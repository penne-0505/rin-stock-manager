from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SyncRecord(BaseModel):
    id: UUID | None = None
    record_type: str  # 対象テーブル名
    payload: dict
    synced: bool
    timestamp: datetime
    user_id: UUID

    def __table_name__() -> str:
        return "sync_records"
