# プロジェクト TODOリスト

## 1. リポジトリ層の具象クラス実装 (`src/repositories/concrete/`)

- [ ] **`menu_repo.py`**
    - [ ] `IMenuItemRepository` の具象クラス実装
    - [ ] `IMenuCategoryRepository` の具象クラス実装
- [ ] **`order_repo.py`**
    - [ ] `IOrderRepository` の具象クラス実装
    - [ ] `IOrderItemRepository` の具象クラス実装
- [ ] **`inventory_repo.py`**
    - [ ] `IMaterialRepository` の具象クラス実装
    - [ ] `IRecipeRepository` の具象クラス実装
    - [ ] `IRecipeMaterialRepository` の具象クラス実装
    - [ ] `IStockRepository` の具象クラス実装
    - [ ] `IStockTakeRepository` の具象クラス実装
    - [ ] `IStockTakeItemRepository` の具象クラス実装
- [ ] **`supplier_repo.py`**
    - [ ] `ISupplierRepository` の具象クラス実装
- [ ] **`user_repo.py`**
    - [ ] `IUserRepository` の具象クラス実装

## 2. ビジネスサービス層の実装 (`src/services/business/`)

- [ ] **`menu_service.py`**
    - [ ] `IMenuService` の具象クラス実装
- [ ] **`order_service.py`**
    - [ ] `IOrderService` の具象クラス実装
- [ ] **`inventory_service.py`**
    - [ ] `IInventoryService` の具象クラス実装
- [ ] **`supplier_service.py`**
    - [ ] `ISupplierService` の具象クラス実装
- [ ] **`user_service.py`**
    - [ ] `IUserService` の具象クラス実装

## 3. UI (Flet) の開発

- [ ] 認証機能のUI実装とサービス連携
- [ ] 在庫管理機能のUI実装とサービス連携
    - [ ] 材料一覧・登録・編集・削除
    - [ ] レシピ一覧・登録・編集・削除
    - [ ] 在庫一覧・更新
    - [ ] 棚卸機能
- [ ] 注文処理機能のUI実装とサービス連携
    - [ ] 注文作成・一覧・詳細表示
- [ ] メニュー管理機能のUI実装とサービス連携
    - [ ] メニュー項目一覧・登録・編集・削除
    - [ ] カテゴリ管理
- [ ] その他必要なUI画面の実装

## 4. テストコードの作成

- [ ] リポジトリ層の単体テスト
    - [ ] 各リポジトリメソッドのテストケース作成
- [ ] サービス層の単体テスト
    - [ ] 各サービスメソッドのテストケース作成 (リポジトリはモック化)
- [ ] サービス層の結合テスト
    - [ ] 実際のDB (Supabase) またはテスト用DBとの連携テスト
- [ ] UI層のテスト (可能な範囲で)

## 5. オフライン機能の統合

- [ ] `FileQueue` を利用したデータ永続化処理のキューイング実装
    - [ ] 各リポジトリの書き込み操作をキューイング対象にする
- [ ] `ReconnectWatcher` と連携したオンライン復帰時のデータ同期処理
    - [ ] キューに溜まった処理の実行
    - [ ] 必要に応じてサーバーからのデータ再取得
- [ ] オフライン時の読み取り操作の考慮 (ローカルキャッシュなど)

## 6. その他

- [ ] 設定ファイル (`config.py`) の整備・拡充
- [ ] エラーハンドリングとロギングの強化
- [ ] ドキュメント作成 (README、コードコメントなど)