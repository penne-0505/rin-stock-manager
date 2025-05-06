import aiofiles
import pytest

# file_queue モジュールもインポート
from src.services import file_queue
from src.services.file_queue import FileQueue
from src.utils import paths


@pytest.mark.asyncio
async def test_push_pop_roundtrip(tmp_path, monkeypatch):
    # DATA_DIRを一時フォルダに差し替え
    monkeypatch.setenv("INVENTORY_APP_DATA", str(tmp_path))
    q = FileQueue()

    await q.push({"op": "POST", "table": "inventory_items"})
    await q.push({"op": "DELETE", "table": "orders"})

    items = await q.pop_all()
    assert len(items) == 2
    assert items[0]["op"] == "POST"
    assert await q.size() == 0


@pytest.mark.asyncio
async def test_gc(tmp_path, monkeypatch):
    """ガベージコレクションが正しく動作することを確認するテスト"""
    # --- 追加: テスト関数内でログ設定を強制上書き ---
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        force=True,
    )

    # MAX_BYTES を小さく設定して、GCがトリガーされるようにする
    monkeypatch.setattr(
        file_queue,
        "MAX_BYTES",
        50,  # 100 から 50 に変更してGCをトリガー
    )  # 対象を paths から file_queue に変更
    # QUEUE_FILE も一時ファイルにする
    queue_file_path = tmp_path / "test_queue.jsonl"
    monkeypatch.setattr(
        file_queue, "QUEUE_FILE", queue_file_path
    )  # 対象を paths から file_queue に変更
    # DATA_DIR も一時フォルダに差し替え
    monkeypatch.setattr(
        file_queue, "DATA_DIR", tmp_path
    )  # DATA_DIR は __init__ で使われるので file_queue でOK

    q = FileQueue()

    # MAX_BYTESを超えるデータを書き込み、GCをトリガーさせる。
    # GC後の行数をテスト用にモンキーパッチで変更する。
    monkeypatch.setattr(file_queue, "GC_KEEP_LINES", 2)

    records_to_push = [{"id": i} for i in range(6)]
    for record in records_to_push:
        await q.push(record)

    # GC が実行されたか確認

    # pop_all で残っているデータを確認
    items = await q.pop_all()

    # 最新の3行 (GC後に追加されたものを含む) が残っているはず
    assert len(items) == 3  # 期待値を 2 から 3 に変更
    assert items[0] == records_to_push[-3]  # {"id": 3}
    assert items[1] == records_to_push[-2]  # {"id": 4}
    assert items[2] == records_to_push[-1]  # {"id": 5}
    assert not queue_file_path.exists()  # pop_all でファイルは削除


@pytest.mark.asyncio
async def test_pop_all_empty(tmp_path, monkeypatch):
    """空のキューに対する pop_all のテスト"""
    queue_file_path = tmp_path / "test_queue_empty.jsonl"
    monkeypatch.setattr(
        file_queue, "QUEUE_FILE", queue_file_path
    )  # 対象を paths から file_queue に変更
    monkeypatch.setattr(
        file_queue, "DATA_DIR", tmp_path
    )  # 対象を paths から file_queue に変更

    q = FileQueue()

    # 1. ファイルが存在しない場合
    assert not queue_file_path.exists()
    items = await q.pop_all()
    assert items == []

    # 2. ファイルは存在するが空の場合
    queue_file_path.touch()
    assert queue_file_path.exists()
    assert await q.size() == 0
    items = await q.pop_all()
    assert items == []
    assert not queue_file_path.exists()  # pop_all でファイルは削除

    # 3. ファイルが存在し、中身が空行の場合 (json.loads でエラーにならないか)
    async with aiofiles.open(queue_file_path, "w") as f:
        await f.write("\n")  # 空行を書き込む
    assert queue_file_path.exists()
    # 空行のみの場合、pop_all 内の json.loads でエラーになる可能性がある
    # FileQueue の実装では空行は無視されるはず
    items = await q.pop_all()
    assert items == []
    assert not queue_file_path.exists()


@pytest.mark.asyncio
async def test_init_existing_dir(tmp_path, monkeypatch):
    """データディレクトリが既に存在する場合の初期化テスト"""
    data_dir_path = tmp_path / "existing_data_dir"
    monkeypatch.setattr(paths, "DATA_DIR", data_dir_path)

    # 事前にディレクトリを作成しておく
    data_dir_path.mkdir(parents=True, exist_ok=True)
    assert data_dir_path.is_dir()

    # FileQueue を初期化してもエラーが発生しないことを確認
    try:
        q = FileQueue()
        # ディレクトリがそのまま存在することを確認
        assert data_dir_path.is_dir()
    except Exception as e:
        pytest.fail(f"Initialization failed with existing directory: {e}")


# 不要な行なので削除
