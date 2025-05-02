# TL;DR

Python (Flet) + Supabase(PostgreSQL) をオンライン時に直接利用し、オフライン時のみ SQLite キャッシュに退避するオフラインファースト在庫管理アプリを開発中。MVP では「在庫操作」「ステータス閲覧」「手動同期」「Google 認証」を実装し、レシート生成・自動同期などは次フェーズへ。

---

## 1. プロジェクト概要

* **目的**: 屋台運営で使う極小規模・社内専用の在庫／売上管理を低コストで実現。
* **対象ユーザー**: 操作担当 2 名 (社内スタッフ)。来店客 約 500 名（アプリ非利用）。
* **要求特性**: 複数端末で同一データを即時共有、オフライン時でも継続利用、ボタン操作の即応性、手動同期。

## 2. 採用技術スタック

| レイヤ       | 技術 / サービス                 | 採用理由                                       |
| --------- | ------------------------- | ------------------------------------------ |
| フロント      | **Flet (Python)**         | 既存 Python スキルを活かし迅速に UI 構築                 |
| クラウド DB   | **Supabase (PostgreSQL)** | 無料枠 + Postgres 互換で将来拡張容易、オンライン CRUD の単一ソース |
| ローカルキャッシュ | **SQLite**                | オフライン時の一時保持・ACID 保証                        |
| データ共有     | **Google Sheets API**     | 非エンジニアとの共有が容易                              |
| 認証        | **Google OAuth2**         | 既存アカウント利用で管理コスト削減                          |

> **ポイント** — 通常時は Supabase を正とし、ネットワーク切断時のみ SQLite へフォールバック。再接続時に差分を Supabase へアップロードして整合性を取る。

## 3. MVP 機能 (確定)

1. **F1 在庫操作ボタン** — 在庫–1 / 売上+1 / オーダー+1 をオンライン時は Supabase へ、オフライン時は SQLite へ保存
2. **F2 ステータス閲覧** — 現在の在庫数・売上を一覧表示（表示ソースは接続状況で切替）
3. **F3 手動同期** — オフラインキャッシュを Supabase ➜ Google Sheets へ送信
4. **F4 Google 認証 & オフライン保持** — OAuth2 ログイン＋ローカルキャッシュ

## 4. ドメインモデル (ドラフト)

```python
class InventoryItem(BaseModel):
    id: str
    name: str
    price: float

class OrderItem(BaseModel):
    inventory_item_id: str
    quantity: int

class Order(BaseModel):
    id: str
    items: List[OrderItem]
    total: float
    timestamp: datetime

class InventoryTransaction(BaseModel):
    id: str
    item_id: str
    change: int  # + 入庫 / – 売上
    type: str    # 'sale' | 'restock'
    timestamp: datetime

class SyncRecord(BaseModel):
    id: str
    record_type: str  # 対象テーブル名
    payload: dict
    synced: bool
    timestamp: datetime
```

## 5. 同期ロジック概要

### オンライン動作

1. CRUD 操作は **直接 Supabase** へ書き込み。
2. （将来）Supabase Realtime で他端末へ変更通知。

### オフライン動作

1. ネットワーク切断検知で「オフラインモード」へ。
2. CRUD 操作は **SQLite + SyncRecord(synced=False)** に退避。
3. 再接続時、「同期」ボタンで未同期レコードをバッチ送信し **`synced=True`** に更新。

## 6. システム構成イメージ

```
            (オンライン)
[Flet UI] ─────────────────▶ [Supabase] ─▶ Edge Function ─▶ Google Sheets
   │
   └──(オフライン)──▶ [SQLite] ←→ SyncRecord
```

## 7. 未決事項 / バックログ

* 自動同期タイミング & バックグラウンドリトライ
* PIN 認証オプション
* レシート (PDF) 生成フォーマット
* 競合解決ポリシー（最終更新優先 など）
* CI/CD & パッケージング方法 (PyInstaller / flet‐pack)
* モニタリング & 無料枠超過アラート設定

## 8. 運用・デプロイ

* **配布形態**: Windows/Mac 用スタンドアロン（PyInstaller 予定）
* **CI/CD**: GitHub Actions でテスト → Build → Release Asset
* **監視**: Supabase ダッシュボード + Google Sheets 変更履歴

## 9. 参考リンク

* Supabase Docs: [https://supabase.com/docs](https://supabase.com/docs)
* Flet Docs: [https://flet.dev/docs](https://flet.dev/docs)
* Google Sheets API Quickstart

---

> **最終更新**: 2025‑05‑02
