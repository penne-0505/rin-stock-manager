from __future__ import annotations

from abc import ABC
from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar, overload

from constants.types import Filter, OrderBy, PKMap
from models.bases._base import CoreBaseModel
from services.platform.client_service import SupabaseClient
from utils.query_utils import apply_filters_to_query, apply_order_by_to_query
from utils.serializers import bulk_serialize_for_supabase, serialize_for_supabase

M = TypeVar("M", bound=CoreBaseModel)
ID = TypeVar("ID")  # 単一主キー値の型（int, str など）


class CrudRepository(ABC, Generic[M, ID]):
    def __init__(
        self,
        client: SupabaseClient,
        model_cls: type[M],
        *,
        pk_cols: Sequence[str] | None = None,  # 複合 PK 対応
    ) -> None:
        self._client = client.supabase_client
        self.model_cls = model_cls
        self.pk_cols: Sequence[str] = pk_cols or ("id",)  # 既定は単一 id
        self.table = self._client.table(self.model_cls.__table_name__())

    # =================================================================
    # internal helpers (private)
    # =================================================================
    def _normalize_key(self, key: ID | PKMap) -> PKMap:
        if isinstance(key, Mapping):
            return key
        # 単一値の場合、pk_cols は 1 列であるはず
        if len(self.pk_cols) != 1:
            raise ValueError(
                "Composite primary key requires a mapping of column→value",
            )
        return {self.pk_cols[0]: key}

    def _apply_pk(self, query: Any, key: PKMap):
        for col in self.pk_cols:
            try:
                query = query.eq(col, key[col])
            except KeyError as exc:
                raise KeyError(
                    f"Missing primary key column '{col}' in key mapping"
                ) from exc
        return query

    # ==================================================================
    # CRUD operations
    # ==================================================================

    # -------- create ---------------------------------------------------
    async def create(self, entity: M) -> M | None:
        serialized_entity = serialize_for_supabase(entity)
        result = await self.table.insert(serialized_entity).execute()
        return self.model_cls.model_validate(result.data[0]) if result.data else None

    async def bulk_create(self, entities: Sequence[M]) -> list[M]:
        if not entities:
            return []
        serialized_entities = bulk_serialize_for_supabase(entities)
        result = await self.table.insert(serialized_entities).execute()
        return (
            [self.model_cls.model_validate(row) for row in result.data]
            if result.data
            else []
        )

    # -------- get ------------------------------------------------------
    @overload
    async def get(self, key: ID) -> M | None:  # 単一キー糖衣
        ...

    @overload
    async def get(self, key: PKMap) -> M | None:  # 複合キー
        ...

    async def get(self, key):  # type: ignore[override]
        pk = self._normalize_key(key)
        row = await self._apply_pk(self.table.select("*"), pk).single().execute()
        return self.model_cls.model_validate(row.data) if row.data else None

    # -------- update ---------------------------------------------------
    @overload
    async def update(self, key: ID, patch: Mapping[str, Any]) -> M | None: ...

    @overload
    async def update(self, key: PKMap, patch: Mapping[str, Any]) -> M | None: ...

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

    async def bulk_delete(self, keys: Sequence[ID | PKMap]) -> None:
        """複数のキーで一括削除"""
        if not keys:
            return

        # 単一カラムPKの場合は効率的なin演算子を使用
        if len(self.pk_cols) == 1:
            pk_col = self.pk_cols[0]
            values = []
            for key in keys:
                normalized = self._normalize_key(key)
                values.append(normalized[pk_col])
            await self.table.delete().in_(pk_col, values).execute()
        else:
            # 複合PKの場合は個別削除（現状の制限）
            for key in keys:
                await self.delete(key)

    # -------- exists ---------------------------------------------------
    @overload
    async def exists(self, key: ID) -> bool: ...

    @overload
    async def exists(self, key: PKMap) -> bool: ...

    async def exists(self, key):  # type: ignore[override]
        pk = self._normalize_key(key)
        rows = await self._apply_pk(self.table.select("1"), pk).limit(1).execute()
        return bool(rows.data)

    # ==================================================================
    # listing & searching
    # ==================================================================
    async def list(self, *, limit: int = 100, offset: int = 0) -> list[M]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        rows = await self.table.select("*").range(offset, offset + limit - 1).execute()
        return (
            [self.model_cls.model_validate(r) for r in rows.data] if rows.data else []
        )

    async def find(
        self,
        filters: Filter | None = None,
        order_by: OrderBy | None = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[M]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        query = self.table.select("*").range(offset, offset + limit - 1)
        if filters:
            query = apply_filters_to_query(query, filters)
        if order_by:
            query = apply_order_by_to_query(query, order_by)
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
