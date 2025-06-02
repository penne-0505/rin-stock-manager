# アーキテクチャガイド

このドキュメントでは、Rin Stock Managerのアーキテクチャ、設計パターン、実装詳細の包括的な概要を提供します。

## 概要

Rin Stock Managerは、関心の分離を持つ階層モジュール構造を実装しています。システムは、明確な責任と依存関係を持つ異なる層にコードを整理しています。

## システム層

```
┌─────────────────────────────────────────┐
│              UI層 (Flet)               │  ← ユーザーインターフェース
├─────────────────────────────────────────┤
│           サービス層                     │  ← ビジネスロジック
├─────────────────────────────────────────┤
│         リポジトリ層                     │  ← データアクセス
├─────────────────────────────────────────┤
│           モデル層                       │  ← データモデル
├─────────────────────────────────────────┤
│     インフラストラクチャ (Supabase)      │  ← データベース
└─────────────────────────────────────────┘
```

### 1. モデル層 (`src/models/`)

検証とシリアライゼーションにPydanticを使用するデータモデル。

**ベースモデル:**
```python
class CoreBaseModel(BaseModel, ABC):
    @classmethod
    @abstractmethod
    def __table_name__(cls) -> str: ...
```

**主要機能:**
- Pydantic検証とシリアライゼーション
- 抽象テーブル名マッピング
- Pythonタイピングによる型安全性
- 不変データ構造

**ドメインモデル:**
- **Analytics**: `DailySummary` - 日次ビジネス指標
- **Inventory**: `Material`, `MaterialCategory`, `Recipe` - 在庫管理
- **Menu**: `MenuItem`, `MenuCategory` - メニュー組織
- **Order**: `Order`, `OrderItem` - 注文処理
- **Stock**: `Purchase`, `PurchaseItem`, `StockAdjustment`, `StockTransaction` - 在庫操作

### 2. リポジトリ層 (`src/repositories/`)

リポジトリ層はデータアクセスを抽象化し、CRUD操作のための一貫したインターフェースを提供します。

#### ベースリポジトリ (`src/repositories/bases/crud_repo.py`)

完全なCRUD操作を持つ汎用リポジトリ:

```python
class CrudRepository(ABC, Generic[M, ID]):
    # CRUD操作
    async def create(self, entity: M) -> M | None
    async def get(self, key: ID | PKMap) -> M | None
    async def update(self, key: ID | PKMap, patch: Mapping[str, Any]) -> M | None
    async def delete(self, key: ID | PKMap) -> None
    async def exists(self, key: ID | PKMap) -> bool
    
    # クエリ操作
    async def list(self, *, limit: int = 100, offset: int = 0) -> list[M]
    async def find(self, filters: Filter | None = None, ...) -> list[M]
    async def count(self, filters: Filter | None = None) -> int
```

**主要機能:**
- モデルとIDのための汎用型サポート
- 複合主キーサポート
- 高度なフィルタリングシステム
- 自動Pydantic検証
- ページ分割サポート

#### ドメインリポジトリ (`src/repositories/domains/`)

各ドメインのための特化されたリポジトリ:

- **`analysis_repo.py`**: 分析とレポート
- **`inventory_repo.py`**: 材料とレシピ管理
- **`menu_repo.py`**: メニュー項目とカテゴリ管理
- **`order_repo.py`**: 注文処理と追跡
- **`stock_repo.py`**: 仕入れと在庫取引管理

### 3. フィルタリングシステム

複雑なクエリをサポートする高度なフィルタリングシステム:

#### フィルタ型

**シンプルフィルタ（ANDロジック）:**
```python
filters = {
    "status": (FilterOp.EQ, "active"),
    "category": (FilterOp.EQ, "electronics")
}
```

**OR条件:**
```python
from utils.filters import OrCondition

or_filter = OrCondition([
    {"status": (FilterOp.EQ, "active")},
    {"status": (FilterOp.EQ, "low_stock")}
])
```

**複合条件:**
```python
complex_filter = ComplexCondition([
    AndCondition({"supplier_id": (FilterOp.EQ, 1)}),
    OrCondition([
        {"status": (FilterOp.EQ, "active")},
        {"status": (FilterOp.EQ, "pending")}
    ])
], operator="and")
```

#### フィルタ操作 (`constants/types.py`)

```python
class FilterOp(Enum):
    EQ = "eq"           # 等しい
    NEQ = "neq"         # 等しくない
    GT = "gt"           # より大きい
    GTE = "gte"         # 以上
    LT = "lt"           # より小さい
    LTE = "lte"         # 以下
    LIKE = "like"       # パターンマッチング
    ILIKE = "ilike"     # 大文字小文字を区別しないパターンマッチング
    IN = "in_"          # リスト内
    IS = "is_"          # nullまたはnot null
```

### 4. サービス層 (`src/services/`)

サービス層にはビジネスロジックが含まれ、リポジトリ操作を調整します。

#### プラットフォームサービス (`src/services/platform/`)

外部統合のためのインフラストラクチャサービス:

- **`client_service.py`**: Supabaseクライアント管理
- **`file_queue.py`**: オフライン操作キューイング
- **`reconnect_watcher.py`**: 接続監視

#### ビジネスサービス (`src/services/business/`)

包括的な機能を持つ完全実装されたドメイン固有のビジネスロジック:

- **`analysis_service.py`**: リアルタイム統計、人気項目ランキング、パフォーマンス指標、材料消費分析を含む分析とレポート
- **`inventory_service.py`**: 材料作成、在庫監視、自動消費/復元、仕入れ記録を含む完全な在庫管理
- **`menu_service.py`**: リアルタイム利用可能性チェック、検索機能、在庫ベース更新を含むメニュー管理
- **`order_service.py`**: 3つのサービスクラスを持つ完全な注文ワークフロー:
  - **CartService**: 検証付きショッピングカート管理
  - **OrderService**: 注文ライフサイクルと履歴管理
  - **KitchenService**: キッチン操作とキュー最適化

### 5. オフラインサポートアーキテクチャ

システムはキューイングメカニズムを通じてオフライン操作をサポートします:

#### FileQueue (`src/services/platform/file_queue.py`)

- オフライン時の書き込み操作をキューイング
- 古い操作の自動ガベージコレクション
- ローカルファイルを使用した永続ストレージ
- スレッドセーフ操作

#### ReconnectWatcher (`src/services/platform/reconnect_watcher.py`)

- ネットワーク接続の監視
- 再接続時のキュー処理のトリガー
- 設定可能な再試行戦略
- イベント駆動アーキテクチャ

**オフラインワークフロー:**
```
1. 操作要求 → 2. 接続チェック
                ↓
3. オンライン: 直接実行
   オフライン: 操作をキュー
                ↓
4. 再接続時 → 5. キューされた操作を処理
```

### 6. 設定管理

Pydantic Settingsを使用した環境ベースの設定:

```python
class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    
    class Config:
        env_file = ".env"
```

**機能:**
- 型検証
- 環境変数サポート
- デフォルト値
- ネストした設定オブジェクト

## 設計パターン

### 1. リポジトリパターン

一貫したインターフェースでデータアクセス操作を提供します。

**実装:**
- 汎用CRUD操作
- 集中化されたクエリロジック
- 一貫したエラーハンドリング
- データベース抽象化層

### 2. ジェネリックプログラミング

型安全な汎用リポジトリとサービス:

```python
class CrudRepository(Generic[M, ID]):
    # M: モデル型
    # ID: 主キー型
```

### 3. 依存性注入

サービスはコンストラクタパラメータを通じてリポジトリインスタンスを受け取ります:

```python
class InventoryService:
    def __init__(self, material_repo: MaterialRepository):
        self.material_repo = material_repo
```

### 4. イベント駆動実装

オフラインサポートは、イベントを通じて接続監視とキュー処理を実装します。

## データフロー

### 読み取り操作
```
UI → サービス → リポジトリ → Supabase → モデル → サービス → UI
```

### 書き込み操作（オンライン）
```
UI → サービス → リポジトリ → Supabase → モデル → サービス → UI
```

### 書き込み操作（オフライン）
```
UI → サービス → FileQueue → ローカルストレージ
                    ↓
ReconnectWatcher → キュー処理 → リポジトリ → Supabase
```

## セキュリティアーキテクチャ

### ユーザー分離

すべてのデータベース操作にはユーザー固有のフィルタリングが含まれます:

```python
async def find_materials(self, user_id: str, filters: Filter = None):
    # クエリに常にuser_idを含める
    user_filter = {"user_id": (FilterOp.EQ, user_id)}
    # 追加フィルタと組み合わせ...
```

### データ検証

- Pydanticモデルがデータ整合性を保証
- すべての層での型検証
- サービスでのビジネスルール検証

## パフォーマンス考慮事項

### クエリ最適化

- データベースレベルでの効率的なフィルタリング
- 大量データセットのページ分割
- 選択的フィールドクエリ
- 接続プーリング

### キャッシュ戦略

- モデルレベルキャッシュ（計画中）
- クエリ結果キャッシュ（計画中）
- オフラインデータ永続化

### スケーラビリティ

- ステートレスサービス設計
- 水平スケーリング能力
- 全体的な非同期操作

## 技術選択

### データベース: Supabase (PostgreSQL)

**理由:**
- PostgreSQLの信頼性とパフォーマンス
- 組み込み認証
- リアルタイム機能
- RESTful API
- オフラインファーストアーキテクチャサポート

### UIフレームワーク: Flet

**理由:**
- Pythonネイティブ開発
- クロスプラットフォーム展開
- モダンUIコンポーネント
- 開発中のホットリロード

### 検証: Pydantic

**理由:**
- 型安全性
- 自動検証
- JSONシリアライゼーション
- パフォーマンス
- IDEサポート

## 将来の拡張

### 計画機能

1. **リアルタイム更新**: ライブデータのためのWebSocket統合
2. **キャッシュ層**: パフォーマンスのためのRedis統合
3. **イベントソーシング**: 監査証跡と状態再構築
4. **マイクロサービス**: スケーラビリティのためのサービス分解
5. **APIゲートウェイ**: 外部APIアクセスとレート制限

### 移行戦略

- データベーススキーマバージョニング
- 後方互換性の維持
- 段階的機能ロールアウト
- データ移行ユーティリティ

このアーキテクチャは、将来の拡張に対する柔軟性を維持しながら、スケーラブルで保守可能なレストラン在庫管理システムのための強固な基盤を提供します。