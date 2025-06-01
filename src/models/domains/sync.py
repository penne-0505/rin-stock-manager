import warnings
from datetime import datetime
from uuid import UUID

from models.bases._base import CoreBaseModel


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
        warnings.warn(
            "Offline SyncRecord not implemented—returns placeholder `table_name`.",
            DeprecationWarning,
        )
        return "sync_records"
