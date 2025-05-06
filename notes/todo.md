# 在庫管理アプリ ─ タスクチェックリスト

## 0. プロジェクト準備 (Week 0‑1)
- [ ] ★0‑1 GitHub Repo 作成（main ブランチ保護・Issue/PR テンプレ）
- [ ] 0‑2 Poetry / venv セットアップ（Python 3.12・supabase‑py・flet 等）
- [ ] 0‑3 CI 雛形（GitHub Actions: pytest + ruff）
- [ ] ★0‑4 Supabase DDL 適用（テーブル / RLS / トリガ作成）
- [ ] ★0‑5 Google OAuth クライアント発行（URI = http://localhost:8550/auth）

## 1. 基盤インフラ (Week 1‑2)
- [ ] ★1‑1 FileQueue 実装（queue.jsonl・5 MB GC・単体テスト）
- [ ] ★1‑2 ReconnectWatcher 実装（5 秒 ping → flush + 指数バックオフ）
- [ ] 1‑3 SupabaseCrudRepository（CRUD + 3 回リトライ）
- [ ] 1‑4 ロギング & .env 読込（logging・python‑dotenv）

## 2. ドメインリポジトリ (Week 2‑3)
- [ ] ★2‑1 InventoryItemRepository（restock / sell）
- [ ] 2‑2 OrderRepository（create_order + 合計計算）
- [ ] 2‑3 InventoryTransactionRepository（log_change）
- [ ] 2‑4 I/F ドキュメント（README に使用例掲載）

## 3. サービス層 & 同期 (Week 3‑4)
- [ ] ★3‑1 InventoryService（在庫操作 + FileQueue enqueue）
- [ ] 3‑2 OrderService（注文登録 + 在庫減算）
- [ ] 3‑3 TransactionService（履歴クエリ）
- [ ] 3‑4 同期フック統合（Services → ReconnectWatcher）

## 4. UI & UX (Week 4‑5)
- [ ] 4‑1 F1 在庫画面（+1/‑1 ボタン・リアルタイム更新）
- [ ] 4‑2 F2 注文画面（アイテム追加・削除・合計表示）
- [ ] 4‑3 F3 履歴画面（DataTable + 期間フィルタ）
- [ ] 4‑4 F4 設定画面（Google ログイン状態）
- [ ] ★4‑5 OfflineBanner 実装（ネット切断時に自動表示）
- [ ] 4‑6 SyncModal 実装（flush 中プログレスバー）

## 5. テスト & パッケージング (Week 5‑6)
- [ ] ★5‑1 E2E シナリオ（オフライン→復帰で入力損失ゼロ）
- [ ] 5‑2 Supabase モック CI（docker‑compose で PostgREST）
- [ ] 5‑3 PyInstaller ビルド（Win/Mac 両 spec）
- [ ] 5‑4 GitHub Release フロー（tag push → artefact 配布）
- [ ] 5‑5 ユーザーマニュアル草案（Markdown / GIF キャプチャ）

## 6. 運用準備 (Week 6‑7)
- [ ] 6‑1 障害復旧手順書（queue 解析・手動 API 送信例）
- [ ] 6‑2 Supabase アラート設定（ストレージ / 帯域しきい値通知）
- [ ] 6‑3 利用ログ集計（任意：supabase.analytics または CloudWatch）
