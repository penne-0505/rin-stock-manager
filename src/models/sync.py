from datetime import datetime
from uuid import UUID

from models.base import CoreBaseModel


class SyncRecord(CoreBaseModel):
    id: UUID | None = None
    record_type: str  # 対象テーブル名
    payload: dict
    synced: bool
    timestamp: datetime
    user_id: UUID | None = None
    completed_at: datetime | None = None

    def __table_name__(self) -> str:
        return "sync_records"
