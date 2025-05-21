from __future__ import annotations

from abc import ABC
from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar, overload

from constants.types import Filter, PKMap
from services.client_service import SupabaseClient
from src.models.base import CoreBaseModel
from utils.query_utils import apply_filters_to_query

T = TypeVar("T", bound=CoreBaseModel)
ID = TypeVar("ID")  # 単一主キー値の型（int, str など）


class CrudRepository(ABC, Generic[T, ID]):
    def __init__(
        self,
        client: SupabaseClient,
        model_cls: type[T],
        *,
        pk_cols: Sequence[str] | None = None,  # 複合 PK 対応
    ) -> None:
        self._client = client.supabase_client
        self.model_cls = model_cls
        self.pk_cols: Sequence[str] = pk_cols or ("id",)  # 既定は単一 id
        self.table = self._client.table(self.model_cls.__table_name__())

    # ---------------------------------------------------------------------
    # internal helpers (private)
    # ---------------------------------------------------------------------
    def _normalize_key(self, key: ID | PKMap) -> PKMap:
        """単一キー値 or キーマッピング → 正規化マッピング"""
        if isinstance(key, Mapping):
            return key
        # 単一値の場合、pk_cols は 1 列であるはず
        if len(self.pk_cols) != 1:
            raise ValueError(
                "Composite primary key requires a mapping of column→value",
            )
        return {self.pk_cols[0]: key}

    def _apply_pk(self, query: Any, key: PKMap):
        """PK 条件をクエリビルダに付与"""
        for col in self.pk_cols:
            try:
                query = query.eq(col, key[col])
            except KeyError as exc:
                raise KeyError(
                    f"Missing primary key column '{col}' in key mapping"
                ) from exc
        return query

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    # -------- create ---------------------------------------------------
    async def create(self, entity: T) -> T | None:
        dumped_entity = entity.model_dump()
        result = await self.table.insert(dumped_entity).execute()
        return self.model_cls.model_validate(result.data[0]) if result.data else None

    # -------- get ------------------------------------------------------
    @overload
    async def get(self, key: ID) -> T | None:  # 単一キー糖衣
        ...

    @overload
    async def get(self, key: PKMap) -> T | None:  # 複合キー
        ...

    async def get(self, key):  # type: ignore[override]
        pk = self._normalize_key(key)
        row = await self._apply_pk(self.table.select("*"), pk).single().execute()
        return self.model_cls.model_validate(row.data) if row.data else None

    # -------- update ---------------------------------------------------
    @overload
    async def update(self, key: ID, patch: Mapping[str, Any]) -> T | None: ...

    @overload
    async def update(self, key: PKMap, patch: Mapping[str, Any]) -> T | None: ...

    async def update(self, key, patch):  # type: ignore[override]
        pk = self._normalize_key(key)
        result = await self._apply_pk(self.table.update(patch), pk).execute()
        return self.model_cls.model_validate(result.data[0]) if result.data else None

    # -------- delete ---------------------------------------------------
    @overload
    async def delete(self, key: ID) -> None: ...

    @overload
    async def delete(self, key: PKMap) -> None: ...

    async def delete(self, key):  # type: ignore[override]
        pk = self._normalize_key(key)
        await self._apply_pk(self.table.delete(), pk).execute()

    # -------- exists ---------------------------------------------------
    @overload
    async def exists(self, key: ID) -> bool: ...

    @overload
    async def exists(self, key: PKMap) -> bool: ...

    async def exists(self, key):  # type: ignore[override]
        pk = self._normalize_key(key)
        rows = await self._apply_pk(self.table.select("1"), pk).limit(1).execute()
        return bool(rows.data)

    # ------------------------------------------------------------------
    # listing & searching
    # ------------------------------------------------------------------
    async def list(self, *, limit: int = 100, offset: int = 0) -> list[T]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        rows = await self.table.select("*").range(offset, offset + limit - 1).execute()
        return (
            [self.model_cls.model_validate(r) for r in rows.data] if rows.data else []
        )

    async def find(
        self,
        filters: Filter | None = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[T]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        query = self.table.select("*").range(offset, offset + limit - 1)
        if filters:
            query = apply_filters_to_query(query, filters)
        rows = await query.execute()
        return (
            [self.model_cls.model_validate(r) for r in rows.data] if rows.data else []
        )

    async def count(self, filters: Filter | None = None) -> int:
        query = self.table.select("id", count="exact", head=True)
        if filters:
            query = apply_filters_to_query(query, filters)
        resp = await query.execute()
        return resp.count  # type: ignore[attr-defined]
