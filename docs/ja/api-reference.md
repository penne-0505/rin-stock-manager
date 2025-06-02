# API リファレンス

このドキュメントでは、Rin Stock Managerのリポジトリとサービスの詳細なAPIリファレンスを提供します。

## リポジトリ層

すべてのリポジトリは`CrudRepository[M, ID]`を継承し、標準的なCRUD操作とドメイン固有のメソッドを提供します。

### 基本CRUD操作

すべてのリポジトリには以下の標準メソッドが含まれています：

```python
# 作成
async def create(entity: M) -> M | None

# 読み取り
async def get(key: ID | PKMap) -> M | None
async def list(*, limit: int = 100, offset: int = 0) -> list[M]
async def find(filters: Filter | None = None, order_by: OrderBy | None = None,
               *, limit: int = 100, offset: int = 0) -> list[M]
async def count(filters: Filter | None = None) -> int

# 更新
async def update(key: ID | PKMap, patch: Mapping[str, Any]) -> M | None

# 削除
async def delete(key: ID | PKMap) -> None

# ユーティリティ
async def exists(key: ID | PKMap) -> bool
```

## 分析リポジトリ

### DailySummaryRepository

日次ビジネスサマリーの分析とレポート機能を提供します。

```python
from repositories.domains.analysis_repo import DailySummaryRepository
```

#### メソッド

##### `find_by_date(target_date: datetime, user_id: UUID) -> DailySummary | None`

特定の日付の日次サマリーを取得します。

**パラメータ:**
- `target_date`: クエリ対象の日付（00:00:00に正規化）
- `user_id`: データ分離のためのユーザー識別子

**戻り値:** 日次サマリーまたは見つからない場合はNone

**例:**
```python
from datetime import datetime
summary = await repo.find_by_date(datetime(2024, 1, 15), user_id)
```

##### `find_by_date_range(date_from: datetime, date_to: datetime, user_id: UUID) -> list[DailySummary]`

日付範囲内のサマリーを取得します。

**パラメータ:**
- `date_from`: 開始日（00:00:00に正規化）
- `date_to`: 終了日（23:59:59に正規化）
- `user_id`: ユーザー識別子

**戻り値:** 日付昇順でソートされたサマリーのリスト

**例:**
```python
summaries = await repo.find_by_date_range(
    datetime(2024, 1, 1),
    datetime(2024, 1, 31),
    user_id
)
```

## 在庫リポジトリ

### MaterialRepository

在庫追跡機能を持つ材料/原材料を管理します。

```python
from repositories.domains.inventory_repo import MaterialRepository
```

#### メソッド

##### `find_by_category_id(category_id: UUID | None, user_id: UUID) -> list[Material]`

カテゴリで材料をフィルタリングします。

**パラメータ:**
- `category_id`: カテゴリフィルタ（Noneの場合すべての材料を返す）
- `user_id`: ユーザー識別子

**戻り値:** 材料のリスト

##### `find_below_alert_threshold(user_id: UUID) -> list[Material]`

在庫補充アラートが必要な材料を検索します。

**戻り値:** アラート閾値を下回る在庫の材料

##### `find_below_critical_threshold(user_id: UUID) -> list[Material]`

重要な在庫不足状況にある材料を検索します。

**戻り値:** 重要閾値を下回る在庫の材料

##### `find_by_ids(material_ids: list[UUID], user_id: UUID) -> list[Material]`

IDによる材料の一括取得。

**パラメータ:**
- `material_ids`: 取得する材料IDのリスト
- `user_id`: ユーザー識別子

**戻り値:** 見つかった材料のリスト

##### `update_stock_amount(material_id: UUID, new_amount: Decimal, user_id: UUID) -> Material | None`

材料の在庫量を更新します。

**パラメータ:**
- `material_id`: 更新する材料
- `new_amount`: 新しい在庫量
- `user_id`: ユーザー識別子

**戻り値:** 更新された材料またはNone

### MaterialCategoryRepository

材料カテゴリを管理します。

##### `find_active_ordered(user_id: UUID) -> list[MaterialCategory]`

表示順序でアクティブなカテゴリを返します。

### RecipeRepository

レシピの材料と関係を管理します。

##### `find_by_menu_item_id(menu_item_id: UUID, user_id: UUID) -> list[Recipe]`

メニュー項目のレシピを取得します。

##### `find_by_material_id(material_id: UUID, user_id: UUID) -> list[Recipe]`

特定の材料を使用するレシピを取得します。

##### `find_by_menu_item_ids(menu_item_ids: list[UUID], user_id: UUID) -> list[Recipe]`

複数のメニュー項目のレシピを一括取得します。

## メニューリポジトリ

### MenuItemRepository

検索とフィルタリング機能を持つメニュー項目を管理します。

```python
from repositories.domains.menu_repo import MenuItemRepository
```

#### メソッド

##### `find_by_category_id(category_id: UUID | None, user_id: UUID) -> list[MenuItem]`

表示順序でカテゴリによりメニュー項目をフィルタリングします。

##### `find_available_only(user_id: UUID) -> list[MenuItem]`

利用可能なメニュー項目のみを返します。

##### `search_by_name(keyword: str | list[str], user_id: UUID) -> list[MenuItem]`

複数キーワードによる高度検索。

**パラメータ:**
- `keyword`: AND検索用の単一キーワードまたはキーワードリスト
- `user_id`: ユーザー識別子

**機能:**
- 大文字小文字を区別しないマッチング
- 複数キーワードのANDロジック
- キーワード正規化

**例:**
```python
# 単一キーワード
items = await repo.search_by_name("pizza", user_id)

# 複数キーワード（ANDロジック）
items = await repo.search_by_name(["chicken", "spicy"], user_id)
```

##### `find_by_ids(menu_item_ids: list[UUID], user_id: UUID) -> list[MenuItem]`

メニュー項目の一括取得。

### MenuCategoryRepository

##### `find_active_ordered(user_id: UUID) -> list[MenuCategory]`

表示順序でアクティブなメニューカテゴリを返します。

## 注文リポジトリ

### OrderRepository

分析機能を持つ完全な注文ライフサイクル管理。

```python
from repositories.domains.order_repo import OrderRepository
```

#### メソッド

##### `find_active_draft_by_user(user_id: UUID) -> Order | None`

アクティブな下書き注文（ショッピングカート）を取得します。

##### `find_by_status_list(status_list: list[OrderStatus], user_id: UUID) -> list[Order]`

複数のステータスで注文をフィルタリングします。

**例:**
```python
from constants.status import OrderStatus
active_orders = await repo.find_by_status_list([
    OrderStatus.DRAFT, 
    OrderStatus.ACTIVE
], user_id)
```

##### `search_with_pagination(filter: Filter, page: int, limit: int) -> tuple[list[Order], int]`

総数付きのページ分割注文検索。

**戻り値:** (注文, 総数)のタプル

##### `find_by_date_range(date_from: datetime, date_to: datetime, user_id: UUID) -> list[Order]`

自動正規化付きの日付範囲フィルタリング。

##### `find_completed_by_date(target_date: datetime, user_id: UUID) -> list[Order]`

特定日の完了注文を取得します。

##### `count_by_status_and_date(target_date: datetime, user_id: UUID) -> dict[OrderStatus, int]`

分析：日付別のステータス別注文数。

**戻り値:** ステータスから数への辞書マッピング

##### `generate_next_order_number(user_id: UUID) -> str`

YYYYMMDD-XXX形式の一意の注文番号を生成します。

**例の結果:** "20241215-001"

##### `find_orders_by_completion_time_range(start_time: datetime, end_time: datetime, user_id: UUID) -> list[Order]`

注文完了時間分析のための分析機能。

### OrderItemRepository

注文明細項目管理。

##### `find_by_order_id(order_id: UUID) -> list[OrderItem]`

注文のすべての項目を取得します。

##### `find_existing_item(order_id: UUID, menu_item_id: UUID) -> OrderItem | None`

既存の注文項目をチェックします（重複検出）。

##### `delete_by_order_id(order_id: UUID) -> bool`

注文項目のカスケード削除。

##### `find_by_menu_item_and_date_range(menu_item_id: UUID, date_from: datetime, date_to: datetime, user_id: UUID) -> list[OrderItem]`

特定メニュー項目の売上分析。

##### `get_menu_item_sales_summary(days: int, user_id: UUID) -> list[dict[str, Any]]`

過去N日間の集計売上分析。

**戻り値:** 売上サマリーデータの辞書リスト

## 在庫リポジトリ

### PurchaseRepository

仕入れ/調達追跡。

```python
from repositories.domains.stock_repo import PurchaseRepository
```

##### `find_recent(days: int, user_id: UUID) -> list[Purchase]`

指定日数内の最近の仕入れ。

##### `find_by_date_range(date_from: datetime, date_to: datetime, user_id: UUID) -> list[Purchase]`

正規化付きの日付範囲フィルタリング。

### PurchaseItemRepository

仕入れ明細項目。

##### `find_by_purchase_id(purchase_id: UUID) -> list[PurchaseItem]`

特定仕入れの項目。

##### `create_batch(purchase_items: list[PurchaseItem]) -> list[PurchaseItem]`

パフォーマンス向上のための一括作成。

### StockAdjustmentRepository

手動在庫調整。

##### `find_by_material_id(material_id: UUID, user_id: UUID) -> list[StockAdjustment]`

材料の調整履歴。

##### `find_recent(days: int, user_id: UUID) -> list[StockAdjustment]`

最近の調整。

### StockTransactionRepository

完全な在庫移動監査証跡。

##### `create_batch(transactions: list[StockTransaction]) -> list[StockTransaction]`

一括取引記録。

##### `find_by_reference(reference_type: str, reference_id: UUID, user_id: UUID) -> list[StockTransaction]`

参照による取引（注文、仕入れなど）。

##### `find_by_material_and_date_range(material_id: UUID, date_from: datetime, date_to: datetime, user_id: UUID) -> list[StockTransaction]`

材料取引履歴。

##### `find_consumption_transactions(date_from: datetime, date_to: datetime, user_id: UUID) -> list[StockTransaction]`

消費分析（負の量のみ）。

## フィルタシステム

### フィルタ操作

```python
from constants.types import FilterOp

# 利用可能な操作
FilterOp.EQ        # 等しい
FilterOp.NEQ       # 等しくない
FilterOp.GT        # より大きい
FilterOp.GTE       # 以上
FilterOp.LT        # より小さい
FilterOp.LTE       # 以下
FilterOp.LIKE      # パターンマッチング
FilterOp.ILIKE     # 大文字小文字を区別しないパターンマッチング
FilterOp.IN        # リスト内
FilterOp.IS        # nullまたはnot null
```

### シンプルフィルタ（ANDロジック）

```python
filters = {
    "status": (FilterOp.EQ, "active"),
    "category_id": (FilterOp.IN, [uuid1, uuid2])
}
```

### OR条件

```python
from utils.filters import OrCondition

or_filter = OrCondition([
    {"status": (FilterOp.EQ, "active")},
    {"status": (FilterOp.EQ, "low_stock")}
])
```

### 複合条件

```python
from utils.filters import ComplexCondition, AndCondition, OrCondition

complex_filter = ComplexCondition([
    AndCondition({"supplier_id": (FilterOp.EQ, 1)}),
    OrCondition([
        {"status": (FilterOp.EQ, "active")},
        {"status": (FilterOp.EQ, "pending")}
    ])
], operator="and")
```

## エラーハンドリング

すべてのリポジトリメソッドは一般的なエラーケースを処理します：

- **空の結果**: 適切に空のリストまたはNoneを返す
- **無効なID**: 適切な例外を発生させる
- **ユーザー分離**: user_id検証によるデータセキュリティの確保
- **型検証**: すべての入力/出力でPydantic検証

## 使用パターン

### リポジトリ初期化

```python
from services.platform.client_service import SupabaseClient
from repositories.domains.inventory_repo import MaterialRepository

client = SupabaseClient()
material_repo = MaterialRepository(client)
```

### 一般的なワークフロー

#### 在庫管理
```python
# 低在庫チェック
low_stock = await material_repo.find_below_alert_threshold(user_id)

# 在庫更新
await material_repo.update_stock_amount(material_id, new_amount, user_id)

# 取引記録
transaction = StockTransaction(...)
await stock_transaction_repo.create(transaction)
```

#### 注文処理
```python
# 下書き注文の取得または作成
draft = await order_repo.find_active_draft_by_user(user_id)

# 項目追加
item = OrderItem(...)
await order_item_repo.create(item)

# 注文完了
await order_repo.update(order_id, {"status": OrderStatus.COMPLETED})
```

#### 分析
```python
# 日次サマリー
summary = await daily_summary_repo.find_by_date(date, user_id)

# 売上分析
sales = await order_item_repo.get_menu_item_sales_summary(30, user_id)
```

## ビジネスサービス層

ビジネスサービス層は、リポジトリの上に構築された高レベルの操作とワークフローを提供します。

### AnalyticsService

包括的な分析とレポート機能を提供します。

```python
from services.business.analysis_service import AnalyticsService
```

#### メソッド

##### `get_real_time_daily_stats(target_date: datetime, user_id: UUID) -> dict[str, Any]`

注文、収益、顧客指標を含むリアルタイム日次統計を返します。

**例:**
```python
stats = await analytics.get_real_time_daily_stats(datetime.now(), user_id)
# 戻り値: {"total_orders": 45, "total_revenue": 1250.00, "avg_order_value": 27.78, ...}
```

##### `get_popular_items_ranking(days: int, user_id: UUID, limit: int = 10) -> list[dict[str, Any]]`

売上量による人気メニュー項目のランキングを返します。

##### `calculate_average_preparation_time(days: int, user_id: UUID) -> float`

パフォーマンス分析のための平均注文準備時間を計算します。

##### `get_material_consumption_analysis(days: int, user_id: UUID) -> list[dict[str, Any]]`

在庫計画のための材料消費パターンを分析します。

### InventoryService

在庫監視、仕入れ、材料消費を含む在庫操作を管理します。

```python
from services.business.inventory_service import InventoryService
```

#### メソッド

##### `create_material(material_data: dict[str, Any], user_id: UUID) -> Material`

検証とデフォルト設定付きで新しい材料を作成します。

**例:**
```python
material = await inventory.create_material({
    "name": "トマト",
    "unit": "kg",
    "current_stock": 50.0,
    "alert_threshold": 10.0,
    "critical_threshold": 5.0
}, user_id)
```

##### `get_stock_alerts_by_level(alert_level: str, user_id: UUID) -> list[Material]`

在庫レベルに基づいて注意が必要な材料を返します。

**パラメータ:**
- `alert_level`: "critical"または"low"

##### `consume_materials_for_order(order_id: UUID, user_id: UUID) -> bool`

注文レシピに基づいて在庫から材料を自動減算します。

##### `record_purchase(purchase_data: dict[str, Any], items: list[dict[str, Any]], user_id: UUID) -> Purchase`

仕入れを記録し、材料在庫レベルを自動更新します。

### MenuService

在庫に基づくリアルタイム利用可能性を持つメニュー管理を扱います。

```python
from services.business.menu_service import MenuService
```

#### メソッド

##### `check_menu_availability(user_id: UUID) -> list[dict[str, Any]]`

現在の在庫レベルに基づいてすべてのメニュー項目の利用可能性をチェックします。

**戻り値:** メニュー項目とその利用可能性ステータスのリスト

##### `calculate_max_servings(menu_item_id: UUID, user_id: UUID) -> int`

利用可能な材料に基づいて最大可能提供数を計算します。

##### `auto_update_menu_availability_by_stock(user_id: UUID) -> int`

在庫レベルに基づいてメニュー項目の利用可能性を自動更新します。

**戻り値:** 更新された項目数

### OrderService (CartService, OrderService, KitchenService)

カート管理からキッチン操作までの完全な注文ワークフロー。

```python
from services.business.order_service import CartService, OrderService, KitchenService
```

#### CartServiceメソッド

##### `get_or_create_active_cart(user_id: UUID) -> Order`

既存のカートを取得するか新しいカートを作成します。

##### `add_item_to_cart(user_id: UUID, menu_item_id: UUID, quantity: int) -> OrderItem`

在庫検証付きでカートに項目を追加します。

##### `calculate_cart_total(cart_id: UUID) -> Decimal`

すべての項目を含むカートの合計金額を計算します。

#### OrderServiceメソッド

##### `checkout_cart(cart_id: UUID, user_id: UUID) -> Order`

カートを確定注文に変換し、在庫消費を処理します。

##### `cancel_order(order_id: UUID, user_id: UUID) -> bool`

注文をキャンセルし、消費した材料を在庫に復元します。

##### `get_order_history(user_id: UUID, page: int = 1, limit: int = 20, filters: dict = None) -> tuple[list[Order], int]`

フィルタリングオプション付きのページ分割注文履歴を取得します。

#### KitchenServiceメソッド

##### `get_kitchen_queue(user_id: UUID) -> list[dict[str, Any]]`

準備詳細付きの優先度付きキッチンキューを返します。

##### `optimize_kitchen_queue(user_id: UUID) -> list[dict[str, Any]]`

準備時間と優先度に基づいて注文順序を最適化します。

##### `calculate_estimated_completion_time(order_id: UUID, user_id: UUID) -> datetime`

キューと準備要件に基づいて注文完了時間を予測します。

## サービス統合パターン

### サービス初期化

```python
from services.platform.client_service import SupabaseClient
from services.business.inventory_service import InventoryService
from repositories.domains.inventory_repo import MaterialRepository

client = SupabaseClient()
material_repo = MaterialRepository(client)
inventory_service = InventoryService(client)
```

### 一般的なワークフロー

#### 完全注文処理
```python
# 1. カートに項目追加
cart = await cart_service.get_or_create_active_cart(user_id)
item = await cart_service.add_item_to_cart(user_id, menu_item_id, quantity)

# 2. チェックアウト
order = await order_service.checkout_cart(cart.id, user_id)

# 3. キッチン処理
queue = await kitchen_service.get_kitchen_queue(user_id)
completion_time = await kitchen_service.calculate_estimated_completion_time(order.id, user_id)
```

#### 在庫管理
```python
# アラートチェック
critical_items = await inventory_service.get_stock_alerts_by_level("critical", user_id)

# 仕入れ記録
purchase = await inventory_service.record_purchase(purchase_data, items, user_id)

# メニュー利用可能性更新
updated = await menu_service.auto_update_menu_availability_by_stock(user_id)
```

#### 分析ダッシュボード
```python
# 日次統計
stats = await analytics_service.get_real_time_daily_stats(datetime.now(), user_id)

# 人気項目
popular = await analytics_service.get_popular_items_ranking(30, user_id)

# パフォーマンス指標
avg_prep_time = await analytics_service.calculate_average_preparation_time(7, user_id)
```