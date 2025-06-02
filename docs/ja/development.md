# 開発ガイド

このガイドでは、Rin Stock Managerプロジェクトの開発ワークフロー、コーディング標準、テスト実践、貢献ガイドラインについて説明します。

## 開発ワークフロー

### ブランチ管理

プロジェクトでは以下のブランチを持つGit Flowを使用します：

- **`main`**: 本番環境対応コード
- **`dev`**: 開発統合ブランチ
- **`feature/*`**: 新機能
- **`bugfix/*`**: バグ修正
- **`hotfix/*`**: 重要な本番修正

### 機能開発

1. **devブランチから開始**:
   ```bash
   git checkout dev
   git pull origin dev
   ```

2. **機能ブランチを作成**:
   ```bash
   git checkout -b feature/inventory-alerts
   ```

3. **変更を加えてコミット**:
   ```bash
   git add .
   git commit -m "feat: 在庫アラート閾値を追加"
   ```

4. **プッシュしてPRを作成**:
   ```bash
   git push origin feature/inventory-alerts
   # devブランチへのPRを作成
   ```

### コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/)に従います：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**種類**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント変更
- `style`: コードスタイル変更
- `refactor`: コードリファクタリング
- `test`: テスト追加
- `chore`: メンテナンスタスク

**例**:
```
feat(inventory): 材料在庫アラートを追加
fix(orders): 注文番号生成問題を解決
docs: フィルタリングのAPIリファレンスを更新
refactor(repo): クエリ構築ロジックを簡素化
```

## コーディング標準

### Pythonスタイルガイド

以下の特定の規約で**PEP 8**に従います：

#### フォーマット
- **行の長さ**: 88文字（Blackのデフォルト）
- **インデント**: 4スペース
- **クォート**: 文字列にダブルクォート
- **インポート**: isortで整理

#### 命名規約
```python
# クラス: PascalCase
class MaterialRepository:

# 関数と変数: snake_case
def find_by_category_id():
async def get_user_materials():

# 定数: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_PAGE_SIZE = 50

# プライベートメソッド: _先頭アンダースコア
def _normalize_key():

# 型変数: 接尾辞付きPascalCase
M = TypeVar("M", bound=CoreBaseModel)
ID = TypeVar("ID")
```

#### 型ヒント

常に型ヒントを使用します：

```python
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

# 関数シグネチャ
async def find_materials(
    user_id: UUID,
    category_id: Optional[UUID] = None,
    limit: int = 100
) -> List[Material]:

# クラス属性
class Material:
    id: UUID
    name: str
    current_stock: Optional[Decimal] = None
```

#### Docstring

Googleスタイルのdocstringを使用します：

```python
async def find_by_date_range(
    self, 
    date_from: datetime, 
    date_to: datetime, 
    user_id: UUID
) -> List[DailySummary]:
    """日付範囲内のサマリーを取得します。
    
    Args:
        date_from: 開始日（00:00:00に正規化）
        date_to: 終了日（23:59:59に正規化）
        user_id: データ分離のためのユーザー識別子
        
    Returns:
        日付昇順でソートされた日次サマリーのリスト
        
    Raises:
        ValueError: date_fromがdate_toより後の場合
    """
```

### リポジトリパターン

#### 標準リポジトリ構造

```python
from repositories.bases.crud_repo import CrudRepository
from models.inventory import Material

class MaterialRepository(CrudRepository[Material, UUID]):
    def __init__(self, client: SupabaseClient):
        super().__init__(client, Material)
    
    # ドメイン固有メソッド
    async def find_by_category_id(
        self, 
        category_id: Optional[UUID], 
        user_id: UUID
    ) -> List[Material]:
        """ユーザー分離でカテゴリ別に材料を検索します。"""
        filters = {"user_id": (FilterOp.EQ, user_id)}
        if category_id is not None:
            filters["category_id"] = (FilterOp.EQ, category_id)
        return await self.find(filters=filters)
```

#### エラーハンドリング

```python
from utils.errors import NotFoundError, ValidationError

async def get_material(self, material_id: UUID, user_id: UUID) -> Material:
    """適切なエラーハンドリングで材料を取得します。"""
    try:
        material = await self.get(material_id)
        if not material:
            raise NotFoundError(f"材料 {material_id} が見つかりません")
        
        # ユーザーアクセスを検証
        if material.user_id != user_id:
            raise ValidationError("アクセスが拒否されました")
            
        return material
    except Exception as e:
        logger.error(f"材料 {material_id} の取得エラー: {e}")
        raise
```

#### ユーザー分離

常にuser_id検証を含めます：

```python
async def find_user_materials(self, user_id: UUID) -> List[Material]:
    """セキュリティのため、すべてのクエリにuser_idを含める必要があります。"""
    return await self.find(filters={"user_id": (FilterOp.EQ, user_id)})
```

### サービス層パターン

#### インターフェース定義

```python
from abc import ABC, abstractmethod

class InventoryServiceInterface(ABC):
    @abstractmethod
    async def get_low_stock_materials(self, user_id: UUID) -> List[Material]:
        """アラート閾値を下回る材料を取得します。"""
        pass
    
    @abstractmethod
    async def adjust_stock(
        self, 
        material_id: UUID, 
        amount: Decimal, 
        reason: str, 
        user_id: UUID
    ) -> Material:
        """監査証跡付きで材料在庫を調整します。"""
        pass
```

#### 実装

```python
class InventoryService(InventoryServiceInterface):
    def __init__(
        self, 
        material_repo: MaterialRepository,
        stock_transaction_repo: StockTransactionRepository
    ):
        self.material_repo = material_repo
        self.stock_transaction_repo = stock_transaction_repo
    
    async def adjust_stock(
        self, 
        material_id: UUID, 
        amount: Decimal, 
        reason: str, 
        user_id: UUID
    ) -> Material:
        """取引ログ付きで実装します。"""
        # 材料在庫を更新
        material = await self.material_repo.update(
            material_id, 
            {"current_stock": amount}
        )
        
        # 取引をログ
        transaction = StockTransaction(
            material_id=material_id,
            amount=amount,
            transaction_type="adjustment",
            reason=reason,
            user_id=user_id
        )
        await self.stock_transaction_repo.create(transaction)
        
        return material
```

## テスト

### テスト構造

```
tests/
├── conftest.py              # Pytest設定
├── test_models/             # モデルテスト
├── test_repositories/       # リポジトリテスト
├── test_services/           # サービステスト
├── test_utils/              # ユーティリティテスト
└── fixtures/                # テストデータ
```

### テスト規約

#### テスト命名

```python
class TestMaterialRepository:
    async def test_find_by_category_id_returns_filtered_materials(self):
        """テストは期待される動作を説明する必要があります。"""
        pass
    
    async def test_find_by_category_id_with_none_returns_all_materials(self):
        """エッジケースをテストします。"""
        pass
    
    async def test_find_by_category_id_with_invalid_user_returns_empty(self):
        """セキュリティシナリオをテストします。"""
        pass
```

#### テスト構造（AAAパターン）

```python
async def test_create_material_success(self):
    """材料作成の成功をテストします。"""
    # Arrange（準備）
    material_data = Material(
        name="テスト材料",
        user_id=test_user_id,
        current_stock=Decimal("100.0")
    )
    
    # Act（実行）
    result = await material_repo.create(material_data)
    
    # Assert（検証）
    assert result is not None
    assert result.name == "テスト材料"
    assert result.user_id == test_user_id
```

#### フィクスチャ

```python
# conftest.py
import pytest
from uuid import uuid4

@pytest.fixture
async def test_user_id():
    """テストユーザーIDを提供します。"""
    return uuid4()

@pytest.fixture
async def material_repo(supabase_client):
    """材料リポジトリを提供します。"""
    return MaterialRepository(supabase_client)

@pytest.fixture
async def sample_material(test_user_id):
    """サンプル材料データを提供します。"""
    return Material(
        name="テスト材料",
        user_id=test_user_id,
        current_stock=Decimal("50.0"),
        alert_threshold=Decimal("10.0")
    )
```

#### モッキング

```python
from unittest.mock import AsyncMock, patch

async def test_service_with_mocked_repository():
    """モックされた依存関係でサービスロジックをテストします。"""
    # Arrange（準備）
    mock_repo = AsyncMock()
    mock_repo.find_below_alert_threshold.return_value = [sample_material]
    
    service = InventoryService(mock_repo)
    
    # Act（実行）
    low_stock = await service.get_low_stock_materials(user_id)
    
    # Assert（検証）
    assert len(low_stock) == 1
    mock_repo.find_below_alert_threshold.assert_called_once_with(user_id)
```

### テストコマンド

```bash
# すべてのテストを実行
poetry run pytest

# 特定のテストファイルを実行
poetry run pytest tests/test_repositories/test_material_repo.py

# カバレッジ付きでテストを実行
poetry run pytest --cov=src --cov-report=html

# パターンマッチするテストを実行
poetry run pytest -k "test_material"

# 詳細出力でテストを実行
poetry run pytest -v

# 最初の失敗で停止してテストを実行
poetry run pytest -x
```

## 開発ツール

### コード品質ツール

#### Black（フォーマット）
```bash
# コードをフォーマット
poetry run black src/ tests/

# フォーマットをチェック
poetry run black --check src/
```

#### isort（インポート整理）
```bash
# インポートを整理
poetry run isort src/ tests/

# インポート整理をチェック
poetry run isort --check-only src/
```

#### Flake8（リンティング）
```bash
# コードをリント
poetry run flake8 src/ tests/

# 特定のルールでリント
poetry run flake8 --max-line-length=88 src/
```

#### mypy（型チェック）
```bash
# 型チェック
poetry run mypy src/

# 設定ファイル付きで型チェック
poetry run mypy --config-file mypy.ini src/
```

### 開発スクリプト

`scripts/dev.py`を作成：

```python
#!/usr/bin/env python3
"""開発ユーティリティスクリプト。"""

import asyncio
import subprocess
import sys
from pathlib import Path

def format_code():
    """blackとisortでコードをフォーマットします。"""
    subprocess.run(["poetry", "run", "black", "src/", "tests/"])
    subprocess.run(["poetry", "run", "isort", "src/", "tests/"])

def lint_code():
    """flake8とmypyでコードをリントします。"""
    result1 = subprocess.run(["poetry", "run", "flake8", "src/", "tests/"])
    result2 = subprocess.run(["poetry", "run", "mypy", "src/"])
    return result1.returncode == 0 and result2.returncode == 0

def run_tests():
    """カバレッジ付きでテストを実行します。"""
    subprocess.run([
        "poetry", "run", "pytest", 
        "--cov=src", 
        "--cov-report=html",
        "--cov-report=term-missing"
    ])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: python scripts/dev.py [format|lint|test]")
        sys.exit(1)
    
    command = sys.argv[1]
    if command == "format":
        format_code()
    elif command == "lint":
        lint_code()
    elif command == "test":
        run_tests()
    else:
        print(f"未知のコマンド: {command}")
        sys.exit(1)
```

## デバッグ

### ログ設定

```python
import logging
from utils.config import settings

# ログを設定
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# コードで使用
logger.info("材料更新を処理中")
logger.warning("在庫が閾値を下回りました")
logger.error("データベース接続に失敗しました", exc_info=True)
```

### デバッグ設定

```python
# 開発設定
if settings.debug:
    # SQLログを有効化
    logging.getLogger('supabase').setLevel(logging.DEBUG)
    
    # 詳細なエラートレースを有効化
    import traceback
    traceback.print_exc()
```

### VS Codeデバッグ設定

`.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        },
        {
            "name": "Python: Test File",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["${file}"],
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        }
    ]
}
```

## パフォーマンスガイドライン

### データベース最適化

```python
# バッチ操作を使用
await repository.create_batch(items)

# クエリ結果を制限
await repository.find(limit=50, offset=0)

# 特定のフィルタを使用
filters = {"status": (FilterOp.EQ, "active")}
await repository.find(filters=filters)

# 必要なフィールドのみを選択（利用可能な場合）
await repository.find(select=["id", "name", "status"])
```

### メモリ管理

```python
# 大きなデータセットにはジェネレータを使用
async def process_materials():
    async for batch in material_repo.find_in_batches(batch_size=100):
        yield batch

# リソースをクリーンアップ
async with AsyncContextManager() as resource:
    await process_data(resource)
```

## ドキュメント

### コードドキュメント

- Googleスタイルのdocstringを使用
- すべてのパブリックメソッドを文書化
- 複雑な機能には例を含める
- ドキュメントを最新の状態に保つ

### APIドキュメント

- 新しいメソッドを追加する際はAPIリファレンスを更新
- 使用例を含める
- エラー条件を文書化
- パラメータ型と戻り値を指定

## 貢献

### プルリクエストプロセス

1. **リポジトリをフォーク**
2. **devから機能ブランチを作成**
3. **コーディング標準に従って変更を実施**
4. **新機能にテストを追加**
5. **ドキュメントを更新**
6. **品質チェックを実行**:
   ```bash
   python scripts/dev.py format
   python scripts/dev.py lint
   python scripts/dev.py test
   ```
7. **説明付きでPRを提出**

### PRレビューチェックリスト

- [ ] コードがスタイルガイドラインに従っている
- [ ] テストが通り、カバレッジが維持されている
- [ ] ドキュメントが更新されている
- [ ] セキュリティ脆弱性がない
- [ ] 破壊的変更が文書化されている
- [ ] パフォーマンスへの影響が考慮されている

### サポート

- **Issues**: 詳細なGitHub issueを作成
- **ディスカッション**: 質問にはGitHub discussionsを使用
- **ドキュメント**: 既存のドキュメントを最初に確認
- **コードレビュー**: レビューのためにメンテナーをタグ付け

この開発ガイドは、チーム全体で一貫した高品質なコードと効率的なコラボレーションを保証します。