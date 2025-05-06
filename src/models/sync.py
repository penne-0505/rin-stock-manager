from datetime import datetime

from pydantic import BaseModel


class SyncRecord(BaseModel):
    id: str
    record_type: str  # 対象テーブル名
    payload: dict
    synced: bool
    timestamp: datetime

    def __table_name__(cls) -> str:
        return "sync_records"
