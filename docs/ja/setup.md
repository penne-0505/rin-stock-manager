# セットアップ・インストールガイド

このガイドでは、Rin Stock Managerの開発環境セットアップとデプロイの準備について説明します。

## 前提条件

### システム要件

- **Python**: 3.12以上
- **Poetry**: 依存関係管理用
- **Git**: バージョン管理用
- **Supabaseアカウント**: データベースと認証用

### プラットフォームサポート

- **主要**: Linux、macOS
- **副次**: Windows（WSL推奨）

## インストール

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd rin-stock-manager
```

### 2. Poetryのインストール

Poetryがインストールされていない場合：

```bash
# curlを使用
curl -sSL https://install.python-poetry.org | python3 -

# pipを使用
pip install poetry

# インストールを確認
poetry --version
```

### 3. 依存関係のインストール

```bash
# すべての依存関係をインストール
poetry install

# 仮想環境をアクティベート
poetry shell
```

### 4. 環境設定

#### 環境ファイルの作成

```bash
cp .env.example .env
```

#### 環境変数の設定

`.env`ファイルを設定で編集：

```env
# Supabase設定
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# オプション: 開発設定
DEBUG=true
LOG_LEVEL=INFO
```

### 5. Supabaseセットアップ

#### Supabaseプロジェクトの作成

1. [Supabase](https://supabase.com)にアクセス
2. 新しいプロジェクトを作成
3. プロジェクトURLと匿名キーをメモ

#### データベーススキーマ

アプリケーションは特定のデータベーステーブルを期待します。SQLを使用して作成：

```sql
-- usersテーブル（Supabase Authを使用しない場合）
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- materialsテーブル
CREATE TABLE materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR NOT NULL,
    category_id UUID REFERENCES material_categories(id),
    current_stock DECIMAL(10,2) DEFAULT 0,
    alert_threshold DECIMAL(10,2),
    critical_threshold DECIMAL(10,2),
    unit VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 材料カテゴリ
CREATE TABLE material_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- メニュー項目
CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    category_id UUID REFERENCES menu_categories(id),
    is_available BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- メニューカテゴリ
CREATE TABLE menu_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 注文
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    order_number VARCHAR UNIQUE NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'draft',
    total_amount DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 注文項目
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    menu_item_id UUID NOT NULL REFERENCES menu_items(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- レシピ
CREATE TABLE recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    menu_item_id UUID NOT NULL REFERENCES menu_items(id),
    material_id UUID NOT NULL REFERENCES materials(id),
    required_amount DECIMAL(10,3) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 仕入れ
CREATE TABLE purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    supplier_name VARCHAR,
    total_amount DECIMAL(10,2),
    purchase_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 仕入れ項目
CREATE TABLE purchase_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_id UUID NOT NULL REFERENCES purchases(id),
    material_id UUID NOT NULL REFERENCES materials(id),
    quantity DECIMAL(10,3) NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 在庫調整
CREATE TABLE stock_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    material_id UUID NOT NULL REFERENCES materials(id),
    adjustment_type VARCHAR NOT NULL,
    amount DECIMAL(10,3) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 在庫取引
CREATE TABLE stock_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    material_id UUID NOT NULL REFERENCES materials(id),
    transaction_type VARCHAR NOT NULL,
    amount DECIMAL(10,3) NOT NULL,
    reference_type VARCHAR,
    reference_id UUID,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 日次サマリー
CREATE TABLE daily_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    summary_date DATE NOT NULL,
    total_orders INTEGER DEFAULT 0,
    total_revenue DECIMAL(10,2) DEFAULT 0,
    total_items_sold INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, summary_date)
);
```

#### 行レベルセキュリティ（RLS）

RLSを有効にしてポリシーを作成：

```sql
-- すべてのテーブルでRLSを有効化
ALTER TABLE materials ENABLE ROW LEVEL SECURITY;
ALTER TABLE material_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_adjustments ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_summaries ENABLE ROW LEVEL SECURITY;

-- ポリシー作成（materialsテーブルの例）
CREATE POLICY "Users can view own materials" 
ON materials FOR SELECT 
USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can create own materials" 
ON materials FOR INSERT 
WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own materials" 
ON materials FOR UPDATE 
USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own materials" 
ON materials FOR DELETE 
USING (auth.uid()::text = user_id::text);

-- すべてのテーブルで同様のポリシーを繰り返す
```

### 6. インストールの確認

```bash
# テストを実行
poetry run pytest

# 依存関係をチェック
poetry show

# Pythonバージョンを確認
python --version
```

## 開発環境セットアップ

### IDE設定

#### VS Code

推奨拡張機能：
- Python
- Pylance
- Python Docstring Generator
- Ruff（リンティング用）

#### 設定

`.vscode/settings.json`を作成：

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

### Gitフック

pre-commitフックをセットアップ：

```bash
# pre-commitをインストール
poetry add --group dev pre-commit

# .pre-commit-config.yamlを作成
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.12
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
        args: ["--profile", "black"]
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
EOF

# フックをインストール
pre-commit install
```

## テストセットアップ

### テスト設定

プロジェクトでは非同期サポート付きのpytestを使用：

```bash
# すべてのテストを実行
poetry run pytest

# カバレッジ付きで実行
poetry run pytest --cov=src

# 特定のテストファイルを実行
poetry run pytest tests/test_repositories.py

# 詳細出力で実行
poetry run pytest -v
```

### テスト環境

テスト環境ファイル`.env.test`を作成：

```env
SUPABASE_URL=your_test_supabase_url
SUPABASE_ANON_KEY=your_test_supabase_key
```

## デプロイの準備

### 本番環境

1. **環境変数**:
   ```env
   SUPABASE_URL=production_url
   SUPABASE_ANON_KEY=production_key
   DEBUG=false
   LOG_LEVEL=WARNING
   ```

2. **依存関係**:
   ```bash
   # 本番依存関係のみをインストール
   poetry install --only=main
   ```

3. **アプリケーションのビルド**:
   ```bash
   # 配布用にビルド
   poetry build
   ```

### Dockerセットアップ（オプション）

`Dockerfile`を作成：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Poetryをインストール
RUN pip install poetry

# 依存関係ファイルをコピー
COPY pyproject.toml poetry.lock ./

# 依存関係をインストール
RUN poetry config virtualenvs.create false \
    && poetry install --only=main

# アプリケーションをコピー
COPY src/ ./src/

# 環境を設定
ENV PYTHONPATH=/app/src

# アプリケーションを実行
CMD ["python", "-m", "src.main"]
```

`docker-compose.yml`を作成：

```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    volumes:
      - ./data:/app/data
    ports:
      - "8000:8000"
```

## トラブルシューティング

### よくある問題

#### Poetryインストール
```bash
# Poetryコマンドが見つからない場合
export PATH="$HOME/.local/bin:$PATH"

# インストールを確認
which poetry
```

#### Pythonバージョン
```bash
# 現在のPythonバージョンをチェック
python --version

# 特定のPythonバージョンをインストール（pyenvを使用）
pyenv install 3.12.0
pyenv global 3.12.0
```

#### Supabase接続
```bash
# 接続をテスト
python -c "
from utils.config import settings
print(f'URL: {settings.supabase_url}')
print(f'Key: {settings.supabase_anon_key[:10]}...')
"
```

#### 依存関係
```bash
# キャッシュをクリアして再インストール
poetry cache clear --all pypi
poetry install --no-cache
```

### 環境の問題

#### 仮想環境
```bash
# アクティブな環境をチェック
poetry env info

# 削除して再作成
poetry env remove python
poetry install
```

#### パスの問題
```bash
# シェルプロファイル（.bashrc、.zshrc）に追加
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### データベースの問題

#### 接続問題
- SupabaseのURLとキーを確認
- Supabaseダッシュボードでプロジェクト状態をチェック
- RLSポリシーが正しく設定されているか確認

#### マイグレーション問題
- テーブル作成スクリプトをチェック
- 外部キー関係を確認
- UUID拡張が有効になっているか確認

## 次のステップ

1. **[開発ガイド](./development.md)を読む** - 貢献ガイドライン
2. **[アーキテクチャガイド](./architecture.md)をチェック** - システム設計
3. **[APIリファレンス](./api-reference.md)をレビュー** - 実装詳細
4. **テストを実行** - すべてが動作することを確認
5. **機能開発を開始** - あなたの機能を開発

## サポート

問題が発生した場合：

1. このトラブルシューティングセクションをチェック
2. エラー詳細についてログをレビュー
3. 環境設定を確認
4. 詳細情報付きでissueを作成