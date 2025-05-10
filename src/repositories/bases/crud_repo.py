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
    """
    Supabaseに対する基本的なCRUD操作を提供するジェネリックリポジトリクラス。

    このクラスは、指定されたSupabaseテーブルに対して、作成、読み取り、更新、削除 (CRUD) の
    基本的な操作を抽象化します。また、フィルタリング、ソート、ページネーションなどの
    クエリユーティリティも提供します。

    Attributes:
        client: Supabaseクライアントインスタンス。
        _table: 操作対象のテーブル名。
    """

    def __init__(self, client: SupabaseClient, table: str) -> None:
        """
        CrudRepositoryのインスタンスを初期化します。

        Args:
            client: Supabaseクライアント。
            table: 操作対象のテーブル名。

        Raises:
            RepositoryError: SupabaseClientが初期化されていない場合。
        """
        if not client.supabase_client:
            raise RepositoryError("SupabaseClient is not initialized.")

        self.client = client.supabase_client
        self._table = table

    # ---------- 基本 CRUD ----------
    async def create(self, entity: T, *, returning: bool = True) -> T | None:
        """
        新しいエンティティを作成します。

        Args:
            entity: 作成するエンティティ。
            returning: 作成されたエンティティを返すかどうか。デフォルトはTrue。

        Returns:
            作成されたエンティティ、またはreturningがFalseの場合はNone。

        Raises:
            ConflictError: エンティティが既に存在する場合など、競合が発生した場合。
            RepositoryError: その他のリポジトリエラー。
        """
        try:
            q = self.client.table(self._table).insert(entity.model_dump())
            if returning:
                data = await q.single()
                return entity.__class__.model_validate(data)
            await q.execute()
            return None
        except Exception as e:
            if isinstance(e, ConflictError):
                raise ConflictError(f"Conflict error: {e}")
            raise RepositoryError(f"Repository error: {e}")

    async def get(self, id_: str, *, for_update: bool = False) -> T | None:
        """
        IDに基づいてエンティティを取得します。

        Args:
            id_: 取得するエンティティのID。
            for_update: 行ロックを取得するかどうか。デフォルトはFalse。

        Returns:
            取得されたエンティティ、または見つからない場合はNone。

        Raises:
            NotFoundError: 指定されたIDのレコードが見つからない場合。
            RepositoryError: その他のリポジトリエラー。
        """
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
        """
        IDに基づいてエンティティを更新します。

        Args:
            id_: 更新するエンティティのID。
            patch: 更新するデータを含む辞書。

        Returns:
            更新されたエンティティ。

        Raises:
            RecordNotFoundError: 指定されたIDのレコードが見つからない場合。
            NotFoundError: 指定されたIDのレコードが見つからない場合 (Supabaseからのエラー)。
            RepositoryError: その他のリポジトリエラー。
        """
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
        """
        IDに基づいてエンティティを削除します。

        Args:
            id_: 削除するエンティティのID。

        Raises:
            NotFoundError: 指定されたIDのレコードが見つからない場合。
            RepositoryError: その他のリポジトリエラー。
        """
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
        """
        フィルタ、ソート順、制限、オフセットに基づいてエンティティのリストを取得します。

        Args:
            filters: 適用するフィルタ。
            order_by: ソート順。
            limit: 取得する最大レコード数。
            offset: スキップするレコード数。

        Returns:
            エンティティのリスト。
        """
        q = self._apply_filters(filters)
        if order_by:
            q = q.order(*order_by) if isinstance(order_by, list) else q.order(order_by)
        if limit:
            q = q.limit(limit, offset or 0)
        data = await q.execute()
        return [self._model_from(d) for d in data]

    async def count(self, *, filters: Filter | None = None) -> int:
        """
        指定されたフィルタに一致するエンティティの数をカウントします。

        Args:
            filters: 適用するフィルタ。

        Returns:
            一致するエンティティの数。
        """
        q = self._apply_filters(filters).select("id", count="exact")
        _, count = await q.execute()
        return count

    async def exists(self, *, filters: Filter | None = None) -> bool:
        """
        指定されたフィルタに一致するエンティティが存在するかどうかを確認します。

        Args:
            filters: 適用するフィルタ。

        Returns:
            エンティティが存在する場合はTrue、そうでない場合はFalse。
        """
        return (await self.count(filters=filters)) > 0

    # ---------- Supabase/PostgREST 特化 ----------
    async def upsert(
        self,
        entity: T,
        *,
        on_conflict: str | list[str] = "id",
        returning: bool = True,
    ) -> T | None:
        """
        エンティティを挿入または更新 (upsert) します。

        Args:
            entity: 挿入または更新するエンティティ。
            on_conflict: 競合が発生した場合の処理方法を指定するカラム名またはカラム名のリスト。デフォルトは "id"。
            returning: 操作されたエンティティを返すかどうか。デフォルトはTrue。

        Returns:
            操作されたエンティティ、またはreturningがFalseの場合はNone。
        """
        q = self.client.table(self._table).upsert(
            entity.model_dump(), on_conflict=on_conflict
        )
        data = await (q.single() if returning else q.execute())
        return None if data is None else self._model_from(data)

    async def rpc(self, func_name: str, params: dict[str, Any]) -> Any:
        """
        SupabaseのRPC (Remote Procedure Call) を実行します。

        Args:
            func_name: 呼び出す関数の名前。
            params: 関数に渡すパラメータ。

        Returns:
            RPC呼び出しの結果。
        """
        return await self.client.rpc(func_name, params).execute()

    # ---------- バルク ----------
    async def bulk_insert(
        self, entities: list[T], *, ignore_conflict: bool = False
    ) -> list[T]:
        """
        複数のエンティティを一括で挿入します。

        Args:
            entities: 挿入するエンティティのリスト。
            ignore_conflict: 競合を無視するかどうか。デフォルトはFalse。

        Returns:
            挿入されたエンティティのリスト。
        """
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
        """
        複数の行を一括で更新または挿入 (upsert) します。

        Args:
            rows: 更新または挿入する行のデータのリスト。各行は辞書形式。
            key: 競合を判断するためのキーとなるカラム名。デフォルトは "id"。

        Returns:
            更新または挿入されたエンティティのリスト。
        """
        if not rows:
            return []
        q = self.client.table(self._table).upsert(rows, on_conflict=key)
        data = await q.execute()
        return [self._model_from(d) for d in data]

    # ---------- ロック ----------
    async def get_for_update(self, id_: str) -> T | None:
        """
        IDに基づいてエンティティを取得し、行ロックをかけます。
        これは `get` メソッドの `for_update=True` のショートカットです。

        Args:
            id_: 取得するエンティティのID。

        Returns:
            取得されたエンティティ、または見つからない場合はNone。
        """
        return await self.get(id_, for_update=True)

    # ---------- 内部ヘルパ ----------
    def _apply_filters(self, filters: Filter | None):
        """
        クエリにフィルタを適用します。

        Args:
            filters: 適用するフィルタ。キーの末尾が "_gte" の場合は ">="、
            "_lte" の場合は "<="、それ以外は "==" として扱われます。

        Returns:
            フィルタが適用されたクエリオブジェクト。
        """
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
        """
        生の辞書データからPydanticモデルのインスタンスを生成します。
        ジェネリック型Tの具体的な型を取得するためのハックを使用しています。

        Args:
            raw: Pydanticモデルに変換する生の辞書データ。

        Returns:
            Pydanticモデルのインスタンス。
        """
        return T.__constraints__[0].model_validate(raw)  # Pydantic generic hack
