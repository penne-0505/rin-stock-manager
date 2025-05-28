from datetime import datetime
from uuid import UUID

from models._base import CoreBaseModel


# 未使用、オフライン対応用
class SyncRecord(CoreBaseModel):
    id: UUID | None = None
    record_type: str  # 対象テーブル名
    payload: dict
    synced: bool
    timestamp: datetime
    user_id: UUID | None = None
    completed_at: datetime | None = None

    @classmethod
    def __table_name__(cls) -> str:
        return "sync_records"
