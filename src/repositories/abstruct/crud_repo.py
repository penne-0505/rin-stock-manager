from __future__ import annotations

from abc import ABC
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from services.app_services.client_service import SupabaseClient
from utils.errors import (
    ConflictError,
    NotFoundError,
    RecordNotFoundError,
    RepositoryError,
)

T = TypeVar("T", bound=BaseModel)


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

    def __init__(self, client: SupabaseClient, table: str, model_cls: type[T]) -> None:
        """
        CrudRepositoryのインスタンスを初期化します。

        Args:
            client: Supabaseクライアント。
            table: 操作対象のテーブル名。
            model_cls: Pydanticモデルクラス。

        Raises:
            RepositoryError: SupabaseClientが初期化されていない場合。
        """
        if not client:
            raise RepositoryError("SupabaseClient is not initialized.")

        self.client = client
        self._table = table
        self._model_cls = model_cls

        self._base_query = self._get_base_query()

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
            # エンティティを挿入
            q = self.client.table(self._table).insert(self._dump(entity))

            # returningがTrueの場合、挿入されたデータを取得
            if returning:
                data = await q.single()
                return self._model_from(data)

            # returningがFalseの場合、挿入を実行
            q.execute()
            return None
        except Exception as e:
            if isinstance(e, ConflictError):
                raise ConflictError(f"Conflict error: {e}")
            raise RepositoryError(f"Repository error: {e}")

    async def read(self, id_: str, *, for_update: bool = False) -> T | None:
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
            # IDに基づいてエンティティを取得
            q = self.client.table(self._table).select("*", count="exact").eq("id", id_)

            # for_updateがTrueの場合、行ロックを取得
            if for_update:
                q = q.filter("", "for_update")  # ←PostgREST拡張SQL

            # クエリを実行してデータを取得
            data = await q.single()
            return None if data is None else self._model_from(data)
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise NotFoundError(f"Record with id {id_} not found.")
            raise RepositoryError(f"Repository error: {e}")

    async def update(
        self, id_: str, patch: dict[str, Any], returning: bool = True
    ) -> T | None:
        """
        IDに基づいてエンティティを更新します。

        Args:
            id_: 更新するエンティティのID。
            patch: 更新するデータを含む辞書。
            returning: 更新されたエンティティを返すかどうか。デフォルトはTrue。

        Returns:
            更新されたエンティティ、returningがFalseの場合はNone。

        Raises:
            RecordNotFoundError: 指定されたIDのレコードが見つからない場合。
            NotFoundError: 指定されたIDのレコードが見つからない場合 (Supabaseからのエラー)。
            RepositoryError: その他のリポジトリエラー。
        """
        try:
            # 更新するデータを辞書形式で取得
            data = await (
                self.client.table(self._table).update(patch).eq("id", id_).single()
            )

            if not data:
                raise RecordNotFoundError(f"Record with id {id_} not found.")
            if not returning:
                return None

            # 取得したデータをモデルに変換して返す
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
            # IDに基づいてエンティティを削除
            await self.client.table(self._table).delete().eq("id", id_).execute()
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise NotFoundError(f"Record with id {id_} not found.")
            raise RepositoryError(f"Repository error: {e}")

    # ---------- クエリユーティリティ ----------
    async def list_entities(
        self,
        *,
        query: Any,
    ) -> list[T]:
        """
        クエリを使用してエンティティのリストを取得します。
        utils/query_utils.pyのQueryFilterUtilsを使用してフィルタリングできます。

        Args:
            query: SQLクエリ文字列。

        Returns:
            取得されたエンティティのリスト。
        """
        # クエリを実行してデータを取得
        data = query.execute()
        result = [self._model_from(d) for d in data]
        return result

    async def count(self, *, query: Any) -> int:
        """
        指定されたクエリに一致するエンティティの数をカウントします。

        Args:
            query: 適用するクエリ。

        Returns:
            一致するエンティティの数。
        """
        # クエリを実行してカウントを取得
        q = query.select("id", count="exact")
        return q.execute()

    async def exists(self, *, query: Any) -> bool:
        """
        指定されたクエリに一致するエンティティが存在するかどうかを確認します。

        Args:
            query: 適用するクエリ。

        Returns:
            エンティティが存在する場合はTrue、そうでない場合はFalse。
        """
        # クエリを実行して存在を確認
        return (await self.count(query=query)) > 0

    # ---------- Supabase/PostgREST 特化 ----------

    async def rpc(self, func_name: str, params: dict[str, Any]) -> Any:
        """
        SupabaseのRPC (Remote Procedure Call) を実行します。

        Args:
            func_name: 呼び出す関数の名前。
            params: 関数に渡すパラメータ。

        Returns:
            RPC呼び出しの結果。
        """
        # SupabaseのRPCを実行
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
        # エンティティを辞書形式に変換
        dumped_entities = [self._dump(e) for e in entities]

        # Supabaseのテーブルに挿入
        if not entities:
            return []
        q = self.client.table(self._table).insert(
            dumped_entities, ignore_duplicates=ignore_conflict
        )
        data = q.execute()
        result = [self._model_from(d) for d in data]
        return result

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

        # 行を更新または挿入
        q = self.client.table(self._table).upsert(rows, on_conflict=key)
        data = q.execute()
        result = [self._model_from(d) for d in data]
        return result

    async def bulk_delete(self, ids: list[str]) -> None:
        """
        複数のエンティティを一括で削除します。

        Args:
            ids: 削除するエンティティのIDのリスト。

        Raises:
            RepositoryError: リポジトリエラー。
        """
        if not ids:
            return

        # IDに基づいてエンティティを削除
        try:
            await self.client.table(self._table).delete().in_("id", ids).execute()
        except Exception as e:
            raise RepositoryError(f"Repository error: {e}")

    async def upsert(
        self, entity: T, *, on_conflict: str = "id", returning: bool = True
    ) -> T | None:
        """
        現在のモデルが対象のテーブルに、レコードを挿入または更新 (upsert) します。

        Args:
            entity: 挿入または更新するエンティティ。
            on_conflict: 競合解決のキーとなるカラム名。デフォルトは "id"。
            returning: 処理後のエンティティを返すかどうか。デフォルトはTrue。

        Returns:
            挿入または更新されたエンティティ、またはreturning=Falseの場合はNone。

        Raises:
            RepositoryError: リポジトリエラー。
        """
        try:
            # エンティティを辞書形式に変換
            q = self.client.table(self._table).upsert(
                self._dump(entity), on_conflict=on_conflict
            )

            # returningがTrueの場合、挿入または更新されたデータを返す
            if returning:
                data = await q.single()
                return self._model_from(data)
            await q.execute()
            return None
        except Exception as e:
            raise RepositoryError(f"Repository error: {e}")

    # ---------- ロック ----------
    async def read_for_update(self, id_: str) -> T | None:
        """
        IDに基づいてエンティティを取得し、行ロックをかけます。
        これは `read` メソッドの `for_update=True` のショートカットです。

        Args:
            id_: 取得するエンティティのID。

        Returns:
            取得されたエンティティ、または見つからない場合はNone。
        """
        return await self.read(id_, for_update=True)

    def _model_from(self, raw: dict[str, Any]) -> T:
        """
        生の辞書データをPydanticモデルに変換します。

        Args:
            raw: 生の辞書データ。

        Returns:
            Pydanticモデルのインスタンス。
        """
        return self._model_cls.model_validate(raw, by_name=True)

    def _dump(self, entity: T) -> dict[str, Any]:
        """
        Pydanticモデルのインスタンスを辞書形式に変換します。

        Args:
            entity: 変換するPydanticモデルのインスタンス。

        Returns:
            辞書形式のデータ。
        """
        return entity.model_dump(by_alias=True)

    def _get_base_query(self) -> Any:
        """
        基本クエリを取得します。

        Returns:
            Supabaseクエリオブジェクト。
        """
        return self.client.table(self._table).select("*")
