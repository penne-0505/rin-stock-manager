# dev_note.md

## `crud_repo.py` 内のクラスの役割と機能

**1. `SyncMeta` クラス**

- **役割:** データ同期に関するメタ情報を保持するための Pydantic モデルです。

- **機能:**
  - レコードの最終更新日時 (`updated_at`) を保持します (デフォルトは現在時刻の UTC)。
  - レコードが同期済みかどうかを示すフラグ (`synced`) を保持します (デフォルトは `False`)。

**2. `AbstractCrudRepository` クラス**

- **役割:** ドメインや特定のデータストア (バックエンド) に依存しない、汎用的な CRUD 操作の契約 (インターフェース) を定義する抽象基底クラス (ABC) です。
- **機能:**
  - 基本的な CRUD 操作 (`create`, `get`, `list`, `update`, `delete`) のための抽象メソッドを宣言します。具象サブクラスはこれらのメソッドを実装する必要があります。
  - 一括操作 (`bulk_upsert`, `bulk_delete`) のデフォルト実装を提供します。
    - `bulk_upsert`: デフォルトでは個別の `update` または `create` を逐次実行します。パフォーマンス向上のためにはサブクラスでのオーバーライドが推奨されます。
    - `bulk_delete`: `asyncio.gather` を使用して個別の `delete` を並行実行します。
  - レコード数をカウントする `count` の抽象メソッドを宣言します。
  - トランザクション処理のための非同期コンテキストマネージャ (`transaction`) を定義します。デフォルト実装は何もしませんが、サブクラスでデータベースの BEGIN/COMMIT などを実装することを意図しています。
  - データ同期をサポートするための抽象メソッド (`unsynced_items`, `mark_synced`) を宣言します。サブクラスは未同期アイテムの取得と同期済みマーク付けのロジックを実装する必要があります。
  - Pydantic モデル (`BaseModel`) を扱うためのジェネリック型 (`T`) を使用します。
  - サブクラスに対して、扱う Pydantic モデルの型 (`model_cls`) を定義することを要求します。

---

## `SupabaseCrudRepository` クラスの役割と機能

- **役割:** Supabase (PostgREST) バックエンドに対する CRUD (作成、読み取り、更新、削除) 操作を抽象化し、標準的なインターフェースを提供します。
- **機能:**
  - 特定の Supabase テーブルに対する CRUD 操作 (`create`, `get`, `list`, `update`, `delete`) を実装します。
  - Supabase Python クライアント (`supabase-py`) を使用して、非同期で Supabase API と通信します。
  - `httpx.HTTPError` 発生時に自動リトライする機能 (`_request` メソッド内) を持ちます。
  - API レスポンスを Pydantic モデル (`model_cls`) に検証・変換します。
  - レコードが見つからない場合 (`RecordNotFoundError`) など、特定のエラーを処理するためのカスタム例外を定義します。
  - 効率的な一括挿入/更新 (`bulk_upsert`) を Supabase の `upsert` 機能を利用して実装します。
  - 一括削除 (`bulk_delete`) を実装します (内部的には個別の削除を並行実行)。
  - 条件に一致するレコード数を取得する `count` メソッドを提供します。
  - サブクラスで `table` (テーブル名) を指定するだけで、基本的な CRUD 操作を利用可能にします。
  - `unsynced_items` と `mark_synced` メソッドを持ちますが、このクラス自体では実質的な処理を行わず、主にインターフェース互換性のために存在します (コメントによると FileQueue 戦略用)。