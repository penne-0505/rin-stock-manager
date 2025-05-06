# 在庫管理アプリ 技術仕様書 v0.1

> **最終更新:** 2025‑05‑03
> **作成:** ChatGPT（o3‑model）

---

## 0. 目的と概要

**在庫管理アプリ**は、中小規模の小売・物販チーム向けに、*Google アカウントで即ログイン*し、複数端末から在庫と売上を一元管理できるデスクトップ / WEB ハイブリッドアプリです。**Supabase (PostgreSQL) をバックエンド**としながら、まれなネットワーク断でも作業を止めないために**FileQueue によるオフライン入力保護**を採用します。

### 0.1 主な特徴

* **在庫・売上をリアルタイム一元管理** – Supabase Realtime で即時反映。

* **オフライン耐性** – 入力はローカル JSON Lines キューに蓄積し、再接続時に自動同期。

* **クロスプラットフォーム** – Flet によりブラウザ / ネイティブの両方をサポート。

* **スプレッドシート同期** – Googleでログインすると、指定のスプレッドシートにDBの内容を同期する機能を搭載。

### 0.2 想定ユーザ

* 小規模店舗オーナー、イベント物販チーム、部活動・サークルの物品管理担当 など。

---

## 1. コア機能セット（MVP 必須 7 機能）

| # | 機能              | 説明                              |
| - | --------------- | ------------------------------- |
| 1 | **在庫操作**        | アイテムを +1/‑1 で増減。売上時は注文に自動集計。    |
| 2 | **注文登録**        | 複数アイテムをまとめて注文化し合計金額を計算。         |
| 3 | **在庫履歴表示**      | 期間フィルタ付き DataTable で変動履歴を閲覧。    |
| 4 | **Google ログイン** | OAuth → Supabase JWT を取得。       |
| 5 | **オフライン入力**     | FileQueue にリクエストを蓄積。復帰後に自動送信。   |
| 6 | **同期インジケータ**    | flush 中はプログレスバー／完了後はバナーを閉じる。    |
| 7 | **自動バックオフ**     | Supabase 429/5xx 時に指数バックオフで再試行。 |

---

## 2. システムアーキテクチャ

```text
┌────────────┐
│    Flet UI      │  ← OfflineBanner / SyncModal
└────────────┘
        │
        ▼
┌────────────┐
│ Service 層   │  InventoryService / OrderService / TransactionService
└────────────┘
        │
        ▼
┌────────────┐
│ Repository 層 │  InventoryItemRepo / OrderRepo / TransactionRepo
│               │  (基底: SupabaseCrudRepository)
└────────────┘
        │  (HTTP)
        ▼
┌────────────┐          ┌────────────┐
│ FileQueue    │  ⇆  │ Supabase REST │
│ (queue.jsonl)│      │  PostgREST   │
└────────────┘          └────────────┘
```

### 2.1 技術スタック

| 分類         | 採用技術                                              |
| ---------- | ------------------------------------------------- |
| 言語 / ランタイム | **Python 3.12**, asyncio                          |
| ドメインモデル    | **Pydantic v2**                                   |
| 永続化        | **Supabase REST (PostgREST)**                     |
| 非同期 HTTP   | **supabase‑py + httpx**                           |
| UI         | **Flet** (デスクトップ & Web)                           |
| オフライン      | **FileQueue** (JSON Lines) + **ReconnectWatcher** |
| CI / CD    | GitHub Actions (`pytest`, `ruff`, PyInstaller)    |

---

## 3. データ保存仕様

| 種別    | パス                             | 備考               |
| ----- | ------------------------------ | ---------------- |
| キュー   | `~/.inventory_app/queue.jsonl` | 追記専用・5 MB 制限     |
| キャッシュ | `~/.inventory_app/cache.json`  | 読み取り専用キャッシュ (任意) |

---

## 4. MVP リリース判定基準

1. **オフライン → 復帰** で入力損失 0 件。
2. 在庫数・売上金額が Supabase 上で整合。
3. PyInstaller 生成バイナリで Windows / macOS 両 OS で正常起動。

---

## 5. フェーズ別タスク一覧（7 フェーズ 32 タスク）

> ★ = ブロッカーになる先行タスク / 依存度の高いタスク
> 週番号はあくまで目安です。実際のスプリント計画に応じて調整してください。

### 0. プロジェクト準備 (Week 0‑1)

| #    | タスク                   | 指示                                        |
| ---- | --------------------- | ----------------------------------------- |
| ★0‑1 | GitHub Repo 作成        | main ブランチ保護・Issue/PR テンプレ                 |
| 0‑2  | Poetry / venv セットアップ  | Python 3.12、`supabase-py`、`flet` 等を追加     |
| 0‑3  | CI 雛形                 | GitHub Actions: `pytest` + `ruff`         |
| ★0‑4 | Supabase DDL 適用       | SQL Editor でテーブル / RLS / トリガ作成            |
| ★0‑5 | Google OAuth クライアント発行 | リダイレクト URI = `http://localhost:8550/auth` |

### 1. 基盤インフラ (Week 1‑2)

| #    | タスク                        | 指示                          |
| ---- | -------------------------- | --------------------------- |
| ★1‑1 | **FileQueue** 実装           | `queue.jsonl`・5 MB GC・単体テスト |
| ★1‑2 | **ReconnectWatcher** 実装    | 5 秒 ping → flush + 指数バックオフ  |
| 1‑3  | **SupabaseCrudRepository** | CRUD + 3 回リトライ (tenacity)   |
| 1‑4  | ロギング & `.env` 読込           | `logging`・`python‑dotenv`   |

### 2. ドメインリポジトリ (Week 2‑3)

| #    | タスク                            | 指示                    |
| ---- | ------------------------------ | --------------------- |
| ★2‑1 | InventoryItemRepository        | `restock` / `sell` 実装 |
| 2‑2  | OrderRepository                | `create_order` + 合計計算 |
| 2‑3  | InventoryTransactionRepository | `log_change`          |
| 2‑4  | I/F ドキュメント                     | README に使用例掲載         |

### 3. サービス層 & 同期 (Week 3‑4)

| #    | タスク                | 指示                          |
| ---- | ------------------ | --------------------------- |
| ★3‑1 | InventoryService   | 在庫操作 + FileQueue enqueue    |
| 3‑2  | OrderService       | 注文登録 + 在庫減算                 |
| 3‑3  | TransactionService | 履歴クエリ提供                     |
| 3‑4  | 同期フック統合            | Services → ReconnectWatcher |

### 4. UI & UX (Week 4‑5)

| #    | タスク              | 指示                 |
| ---- | ---------------- | ------------------ |
| 4‑1  | F1 在庫画面          | +1/‑1 ボタン・リアルタイム更新 |
| 4‑2  | F2 注文画面          | アイテム追加・削除・合計表示     |
| 4‑3  | F3 履歴画面          | DataTable + 期間フィルタ |
| 4‑4  | F4 設定画面          | Google ログイン状態・環境変数 |
| ★4‑5 | OfflineBanner 実装 | ネット切断時に自動表示        |
| 4‑6  | SyncModal 実装     | flush 中プログレスバー     |

### 5. テスト & パッケージング (Week 5‑6)

| #    | タスク             | 指示                         |
| ---- | --------------- | -------------------------- |
| ★5‑1 | E2E シナリオ        | オフライン→復帰で入力損失ゼロ            |
| 5‑2  | Supabase モック CI | docker‑compose で PostgREST |
| 5‑3  | PyInstaller ビルド | Win/Mac 両 spec 生成          |
| 5‑4  | GH Release フロー  | tag push → artefact 配布     |
| 5‑5  | ユーザーマニュアル       | Markdown + GIF キャプチャ       |

### 6. 運用準備 (Week 6‑7)

| #   | タスク             | 指示                                  |
| --- | --------------- | ----------------------------------- |
| 6‑1 | 障害復旧手順書         | queue 解析・手動 API 送信例                 |
| 6‑2 | Supabase アラート設定 | ストレージ/帯域しきい値通知                      |
| 6‑3 | 利用ログ集計 (任意)     | `supabase.analytics` または CloudWatch |

---

## 6. 当面のアクション (Top 5)

1. **GitHub Repo & CI** 初期化
2. **Supabase DDL** を Studio で実行
3. **Google OAuth** 発行 → `.env` に設定
4. **FileQueue** 実装＆`pytest` グリーン
5. **ReconnectWatcher** と仮 UI バナーでオフライン復帰を検証

---

## 7. 開発規約（抜粋）

* **Git flow** 準拠。`main` 直 push 禁止、PR 必須。
* コードは **PEP 8 + ruff** 準拠、**mypy** を将来的に導入。
* コミットメッセージは *Convention Commit*。例: `feat(queue): add gc for >5MB`。
* `.env` に機密キー (`SUPABASE_SERVICE_ROLE`) を**絶対にコミットしない**。

---

## 8. 用語集

| 用語                   | 意味                                         |
| -------------------- | ------------------------------------------ |
| **FileQueue**        | オフライン中の API コールを JSON Lines で保持するローカルキュー。  |
| **ReconnectWatcher** | ネット復帰を監視し FileQueue を flush するバックグラウンドタスク。 |
| **PostgREST**        | Supabase が提供する PostgreSQL → REST 自動変換レイヤ。  |
| **Flush**            | キュー内レコードを Supabase に送信し、成功したら削除する処理。       |

---

## 9. 参考リンク

* Supabase Docs — [https://supabase.com/docs](https://supabase.com/docs)
* Flet Documentation — [https://flet.dev](https://flet.dev)
* Pydantic v2 — [https://docs.pydantic.dev](https://docs.pydantic.dev)

---

以上が **在庫管理アプリ MVP 概要 & タスク全容** です。アップデートやご質問は Slack #inventory-app までお知らせください。
