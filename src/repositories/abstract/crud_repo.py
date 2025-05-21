from abc import ABC
from typing import Any, Generic, Mapping, TypeVar

from constants.types import Filter
from services.client_service import SupabaseClient
from src.models.base import CoreBaseModel
from utils.query_utils import apply_filters_to_query

# モデル・ID型の定義
T = TypeVar("T", bound=CoreBaseModel)
ID = TypeVar("ID")


class CrudRepository(ABC, Generic[T, ID]):
    def __init__(self, client: SupabaseClient, model_cls: type[T]) -> None:
        # クライアントを初期化 -> テーブルを取得
        self.client = client.supabase_client
        self.model_cls = model_cls
        self.table = self.client.table(self.model_cls.__table_name__())

    async def create(self, entity: T) -> T | None:
        dumped_entity = entity.model_dump()
        result = await self.table.insert(dumped_entity).execute()
        return self.model_cls.model_validate(result.data[0]) if result.data else None

    async def get(self, id: ID) -> T | None:
        row = await self.table.select("*").eq("id", id).single().execute()
        return self.model_cls.model_validate(row.data) if row.data else None

    async def update(self, id: ID, patch: Mapping[str, Any]) -> T | None:
        result = await self.table.update(patch).eq("id", id).execute()
        return self.model_cls.model_validate(result.data[0]) if result.data else None

    async def delete(self, id: ID) -> None:
        await self.table.delete().eq("id", id).execute()

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[T]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        rows = await self.table.select("*").range(offset, offset + limit - 1).execute()

        return (
            [self.model_cls.model_validate(row) for row in rows.data]
            if rows.data
            else []
        )

    async def find(
        self, filters: Filter | None = None, limit: int = 100, offset: int = 0
    ) -> list[T]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        base_query = self.table.select("*").range(offset, limit + offset - 1)

        # もしフィルタが指定されていたら、クエリに追加
        if filters:
            base_query = apply_filters_to_query(base_query, filters)

        # クエリを実行
        rows = await base_query.execute()

        # 結果をモデルに変換して返す
        return (
            [self.model_cls.model_validate(row) for row in rows.data]
            if rows.data
            else []
        )

    async def exists(self, id: ID) -> bool:
        rows = await self.table.select("id").eq("id", id).maybe_single().execute()
        return bool(rows.data)

    async def count(self, filters: Filter | None = None) -> int:
        query = self.table.select("id", count="exact", head=True)
        if filters:
            query = apply_filters_to_query(query, filters)
        resp = await query.execute()
        return resp.count  # ← supabase-py の Response.count
