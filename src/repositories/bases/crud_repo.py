from __future__ import annotations

from abc import ABC
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from services.client_service import SupabaseClient
from utils.errors import (
    ConflictError,
    NotFoundError,
    RecordNotFoundError,
    RepositoryError,
)

T = TypeVar("T", bound=BaseModel)

Filter = dict[str, Any]  # e.g. {"user_id": "xxx", "date_gte": "2025-05-01"}
OrderBy = str | list[str] | None  # "date.desc", ["date", "created_at.desc"]


class CrudRepository(ABC, Generic[T]):
    def __init__(self, client: SupabaseClient, table: str) -> None:
        if not client.supabase_client:
            raise RepositoryError("SupabaseClient is not initialized.")

        self.client = client.supabase_client
        self._table = table

    # ---------- 基本 CRUD ----------
    async def create(self, entity: T, *, returning: bool = True) -> T | None:
        try:
            q = self.client.table(self._table).insert(entity.model_dump())
            if returning:
                data = await q.single()
                return entity.__class__.parse_obj(data)
            await q.execute()
            return None
        except Exception as e:
            if isinstance(e, ConflictError):
                raise ConflictError(f"Conflict error: {e}")
            raise RepositoryError(f"Repository error: {e}")

    async def get(self, id_: str, *, for_update: bool = False) -> T | None:
        try:
            q = self.client.table(self._table).select("*", count="exact").eq("id", id_)
            if for_update:
                q = q.filter("", "for_update")  # ←PostgREST拡張SQL
            data = await q.single()
            return None if data is None else self._model_from(data)
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise NotFoundError(f"Record with id {id_} not found.")
            raise RepositoryError(f"Repository error: {e}")

    async def update(self, id_: str, patch: dict[str, Any]) -> T:
        try:
            data = await (
                self.client.table(self._table).update(patch).eq("id", id_).single()
            )
            if not data:
                raise RecordNotFoundError(f"Record with id {id_} not found.")
            return self._model_from(data)
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise NotFoundError(f"Record with id {id_} not found.")
            raise RepositoryError(f"Repository error: {e}")

    async def delete(self, id_: str) -> None:
        try:
            await self.client.table(self._table).delete().eq("id", id_).execute()
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise NotFoundError(f"Record with id {id_} not found.")
            raise RepositoryError(f"Repository error: {e}")

    # ---------- クエリユーティリティ ----------
    async def list(
        self,
        *,
        filters: Filter | None = None,
        order_by: OrderBy | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[T]:
        q = self._apply_filters(filters)
        if order_by:
            q = q.order(*order_by) if isinstance(order_by, list) else q.order(order_by)
        if limit:
            q = q.limit(limit, offset or 0)
        data = await q.execute()
        return [self._model_from(d) for d in data]

    async def count(self, *, filters: Filter | None = None) -> int:
        q = self._apply_filters(filters).select("id", count="exact")
        _, count = await q.execute()
        return count

    async def exists(self, *, filters: Filter | None = None) -> bool:
        return (await self.count(filters=filters)) > 0

    # ---------- Supabase/PostgREST 特化 ----------
    async def upsert(
        self,
        entity: T,
        *,
        on_conflict: str | list[str] = "id",
        returning: bool = True,
    ) -> T | None:
        q = self.client.table(self._table).upsert(
            entity.model_dump(), on_conflict=on_conflict
        )
        data = await (q.single() if returning else q.execute())
        return None if data is None else self._model_from(data)

    async def rpc(self, func_name: str, params: dict[str, Any]) -> Any:
        return await self.client.rpc(func_name, params).execute()

    # ---------- バルク ----------
    async def bulk_insert(
        self, entities: list[T], *, ignore_conflict: bool = False
    ) -> list[T]:
        if not entities:
            return []
        q = self.client.table(self._table).insert(
            [e.model_dump() for e in entities], ignore_duplicates=ignore_conflict
        )
        data = await q.execute()
        return [self._model_from(d) for d in data]

    async def bulk_update(
        self,
        rows: list[dict[str, Any]],
        *,
        key: str = "id",
    ) -> list[T]:
        if not rows:
            return []
        q = self.client.table(self._table).upsert(rows, on_conflict=key)
        data = await q.execute()
        return [self._model_from(d) for d in data]

    # ---------- ロック ----------
    async def get_for_update(self, id_: str) -> T | None:
        return await self.get(id_, for_update=True)

    # ---------- 内部ヘルパ ----------
    def _apply_filters(self, filters: Filter | None):
        q = self.client.table(self._table).select("*")
        if filters:
            for k, v in filters.items():
                if k.endswith("_gte"):
                    q = q.gte(k[:-4], v)
                elif k.endswith("_lte"):
                    q = q.lte(k[:-4], v)
                else:
                    q = q.eq(k, v)
        return q

    @staticmethod
    def _model_from(raw: dict[str, Any]) -> T:  # type: ignore[override]
        return T.__constraints__[0].parse_obj(raw)  # Pydantic generic hack
