import json
from pathlib import Path

import aiofiles
import pytest
import pytest_asyncio

from src.services.file_queue import FileQueue

# from src.utils.paths import MAX_BYTES as DEFAULT_MAX_BYTES # このファイルでは未使用
# from src.utils.paths import QUEUE_FILE as DEFAULT_QUEUE_FILE # このファイルでは未使用

# pytest-asyncio が 'auto' モードで実行されるようにする
pytest_plugins = ("pytest_asyncio",)


@pytest_asyncio.fixture
async def queue(tmp_path: Path):  # monkeypatch を削除
    """テスト用のFileQueueインスタンスと一時的なキューファイルパスを提供するフィクスチャ"""
    test_queue_file = (
        tmp_path / "test_queue_basic.jsonl"
    )  # ファイル名を変更して衝突を避ける
    # monkeypatch.setattr("src.utils.paths.QUEUE_FILE", test_queue_file) # 削除
    # test_data_dir = tmp_path / "data_basic"  # ディレクトリ名も変更 # 削除
    # monkeypatch.setattr("src.utils.paths.DATA_DIR", test_data_dir) # 削除

    q = FileQueue(queue_file_path=test_queue_file)  # コンストラクタでパスを指定
    yield q
    # aiofiles.os を使用して非同期的にファイル操作を行う
    if await aiofiles.os.path.exists(test_queue_file):
        await aiofiles.os.remove(test_queue_file)


@pytest.mark.asyncio
async def test_push_and_pop_all_single_record(queue: FileQueue):
    """単一レコードのpushとpop_allのテスト"""
    record = {"id": 1, "data": "test_data_1"}
    await queue.push(record)

    items = await queue.pop_all()
    assert len(items) == 1
    assert items[0] == record
    assert not queue.queue_file.exists()  # queue.QUEUE_FILE を queue.queue_file に変更


@pytest.mark.asyncio
async def test_push_and_pop_all_multiple_records(queue: FileQueue):
    """複数レコードのpushとpop_allのテスト"""
    records = [
        {"id": 1, "data": "test_data_1"},
        {"id": 2, "data": "test_data_2"},
        {"id": 3, "data": "test_data_3"},
    ]
    for record in records:
        await queue.push(record)

    items = await queue.pop_all()
    assert len(items) == len(records)
    assert items == records
    assert not queue.queue_file.exists()  # queue.QUEUE_FILE を queue.queue_file に変更


@pytest.mark.asyncio
async def test_pop_all_empty_queue(queue: FileQueue):
    """空のキューに対するpop_allのテスト"""
    items = await queue.pop_all()
    assert len(items) == 0
    assert not queue.queue_file.exists()  # queue.QUEUE_FILE を queue.queue_file に変更


@pytest.mark.asyncio
async def test_size_empty_queue(queue: FileQueue):
    """空のキューのサイズのテスト"""
    size = await queue.size()
    assert size == 0


@pytest.mark.asyncio
async def test_size_after_push(queue: FileQueue):
    """レコード追加後のキューサイズのテスト"""
    record = {"id": 1, "data": "test_data"}
    await queue.push(record)
    expected_size = len(json.dumps(record).encode("utf-8")) + 1  # +1 for newline
    size = await queue.size()
    assert size == expected_size
