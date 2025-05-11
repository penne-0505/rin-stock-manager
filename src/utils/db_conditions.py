from typing import Any

Filter = dict[str, Any]  # e.g. {"user_id": "xxx", "date_gte": "2025-05-01"}
OrderBy = str | list[str] | None  # "date.desc", ["date", "created_at.desc"]
