### 1. 注文の作成

- **入力**: user\_id, items (List\[OrderItem])
- **処理**:
	- 各在庫アイテムの在庫数チェック
	- 合計金額計算
	- Order + OrderItem 登録
	- 在庫トランザクション追加（出庫）
	- 同期レコード作成
- **出力**: 作成された注文データ
- **レイヤ担当**:
	- サービス: 全体の制御
	- OrderRepository: insert
	- InventoryRepository: 在庫更新 + transaction記録
	- SyncRepository: insert
---
### 2. 注文一覧の取得（ステータス別）
- **入力**: ステータス, 日付範囲, ユーザーID
- **処理**: フィルタ付きで注文リストを取得
- **出力**: List\[Order]
- **レイヤ担当**:
	- OrderRepository: list(filter=...)
---
### 3. 注文詳細の取得
- **入力**: order\_id
- **処理**: IDに該当するOrderとそのOrderItemsを取得
- **出力**: Order
- **レイヤ担当**:
	- OrderRepository: get + join or fetch related
---
### 4. 注文の編集
- **入力**: order\_id, patch (items or status)
- **処理**:
	- Orderの更新（例：status）
	- 在庫の補正が必要な場合、トランザクション再登録
- **出力**: 更新後のOrder
- **レイヤ担当**:
	- サービス: 複合更新処理制御
	- OrderRepository: update
	- InventoryRepository: stock補正・transaction調整

---
### 5. 注文の削除

- **入力**: order\_id
- **処理**:
	- Orderの削除
	- 在庫を巻き戻す（optional）
	- OrderItemの削除
- **出力**: 成功ステータス
- **レイヤ担当**:
	- サービス: 一括制御
	- OrderRepository: delete
	- InventoryRepository: rollback在庫（optional）

---
### 6. ステータス変更
- **入力**: order\_id, new\_status
- **処理**: Orderのstatusフィールドを変更
- **出力**: 更新済みOrder
- **レイヤ担当**:
	- OrderRepository: update

---
### 7. ステータス別注文カウント
- **入力**: status
- **処理**: statusでcount()
- **出力**: 件数 (int)
- **レイヤ担当**:
	- OrderRepository: count(filter=...)

---
### 8. 在庫アイテムの追加
- **入力**: name, price, stock
- **処理**: InventoryItemの登録
- **出力**: InventoryItem
- **レイヤ担当**:
	- InventoryRepository: insert

---
### 9. 在庫アイテムの編集
- **入力**: item\_id, patch
- **処理**: InventoryItemの更新
- **出力**: InventoryItem
- **レイヤ担当**:
	- InventoryRepository: update

---
### 10. 在庫アイテムの削除
- **入力**: item\_id
- **処理**: InventoryItemの削除
- **出力**: 成功ステータス
- **レイヤ担当**:
	- InventoryRepository: delete

---
### 11. 在庫残数の取得
- **入力**: item\_id
- **処理**: itemのstockを取得
- **出力**: stock数
- **レイヤ担当**:
	- InventoryRepository: get

---
### 12. 在庫履歴の登録（売上/入庫）
- **入力**: item\_id, change, type, user\_id
- **処理**:
	- InventoryTransactionの登録
	- InventoryItemのstockを更新
- **出力**: InventoryTransaction
- **レイヤ担当**:
	- サービス or InventoryRepository: 一括処理

---
### 13. トランザクション履歴一覧取得
- **入力**: item\_id or user\_id, 日付フィルター
- **処理**: 条件でInventoryTransactionをリスト取得
- **出力**: List\[InventoryTransaction]
- **レイヤ担当**:
	- InventoryRepository: list(filter=...)

---
### 14. 同期レコードの記録
- **入力**: record\_type, payload, user\_id
- **処理**: SyncRecord insert
- **出力**: SyncRecord
- **レイヤ担当**:
	- SyncRepository: insert

---
### 15. 同期済みレコード一覧取得
- **入力**: user\_id, synced=True
- **処理**: 条件付きlist取得
- **出力**: List\[SyncRecord]
- **レイヤ担当**:
	- SyncRepository: list(filter=...)

---
### 16. Googleスプレッドシートエクスポート（将来）
- **入力**: ユーザーIDまたは対象データ
- **処理**:
	- 対象データを選定
	- スプレッドシート形式に整形
	- Google APIで送信
- **出力**: 成功ステータス or URL
- **レイヤ担当**:
	- サービス: データ整形 + 外部送信
	- 各Repository: データ抽出
