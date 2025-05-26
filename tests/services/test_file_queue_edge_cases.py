import asyncio
import json
from pathlib import Path

import aiofiles
import pytest
import pytest_asyncio

from src.services.file_queue import FileQueue

# from src.utils.paths import MAX_BYTES as DEFAULT_MAX_BYTES # このファイルでは未使用
# from src.utils.paths import QUEUE_FILE as DEFAULT_QUEUE_FILE # このファイルでは未使用

pytest_plugins = ("pytest_asyncio",)


@pytest_asyncio.fixture
async def queue(tmp_path: Path):  # monkeypatch を削除
    """テスト用のFileQueueインスタンスと一時的なキューファイルパスを提供するフィクスチャ"""
    test_queue_file = tmp_path / "test_queue_edge.jsonl"  # ファイル名を変更
    # monkeypatch.setattr("src.utils.paths.QUEUE_FILE", test_queue_file) # 削除
    # test_data_dir = tmp_path / "data_edge"  # ディレクトリ名も変更 # 削除
    # monkeypatch.setattr("src.utils.paths.DATA_DIR", test_data_dir) # 削除

    q = FileQueue(queue_file_path=test_queue_file)  # コンストラクタでパスを指定
    yield q
    # aiofiles.os を使用して非同期的にファイル操作を行う
    if await aiofiles.os.path.exists(test_queue_file):
        await aiofiles.os.remove(test_queue_file)


@pytest.mark.asyncio
async def test_pop_all_with_invalid_json_lines(queue: FileQueue):
    """不正なJSON行が含まれる場合のpop_allのテスト"""
    valid_record1 = {"id": 1, "data": "valid_1"}
    valid_record2 = {"id": 2, "data": "valid_2"}
    invalid_line = "this is not a json line\n"

    # 手動でファイルに書き込む
    queue_file_path = queue.queue_file  # queue.QUEUE_FILE を queue.queue_file に変更
    # aiofiles を使って非同期で書き込む
    async with aiofiles.open(
        queue_file_path, "w", encoding="utf-8"
    ) as f:  # aiofiles.open を使用
        await f.write(json.dumps(valid_record1) + "\n")  # await を追加
        await f.write(invalid_line)  # await を追加
        await f.write(json.dumps(valid_record2) + "\n")  # await を追加

    items = await queue.pop_all()
    assert len(items) == 2
    assert valid_record1 in items
    assert valid_record2 in items
    assert not queue_file_path.exists()  # asyncio.to_thread を削除


@pytest.mark.asyncio
async def test_concurrent_push_and_pop(tmp_path: Path, monkeypatch):
    """複数のコルーチンからの同時pushとpop_allのテスト（基本的な競合状態の確認）"""
    # このテストは FileQueue の基本的なスレッドセーフティや
    # asyncio のロック機構に依存する部分を厳密にテストするものではなく、
    # 通常の利用シーンでの基本的な動作確認を目的とします。

    # このテストケース専用のキューファイルとデータディレクトリを設定
    concurrent_test_queue_file = tmp_path / "concurrent_queue.jsonl"
    # monkeypatch.setattr("src.utils.paths.QUEUE_FILE", concurrent_test_queue_file) # 削除
    # concurrent_test_data_dir = tmp_path / "data_concurrent" # 削除
    # monkeypatch.setattr("src.utils.paths.DATA_DIR", concurrent_test_data_dir) # 削除

    # このテストケース専用のFileQueueインスタンスを作成
    # これにより、他のテストケースのフィクスチャ `queue` とは独立した状態となる
    queue_instance = FileQueue(
        queue_file_path=concurrent_test_queue_file
    )  # コンストラクタでパスを指定

    num_pusher_tasks = 5
    records_per_pusher = 10
    total_records = num_pusher_tasks * records_per_pusher

    async def pusher(start_id):
        for i in range(records_per_pusher):
            await queue_instance.push(
                {"id": start_id + i, "data": f"data_{start_id + i}"}
            )
            await asyncio.sleep(0.001)  # わずかな遅延で競合の可能性を少し高める

    pusher_tasks = []
    for i in range(num_pusher_tasks):
        pusher_tasks.append(asyncio.create_task(pusher(i * records_per_pusher)))

    await asyncio.gather(*pusher_tasks)

    all_items = await queue_instance.pop_all()

    assert len(all_items) == total_records
    assert len(set(item["id"] for item in all_items)) == total_records

    # クリーンアップ
    if await aiofiles.os.path.exists(
        concurrent_test_queue_file
    ):  # aiofiles.os.path.exists を使用
        await aiofiles.os.remove(
            concurrent_test_queue_file
        )  # aiofiles.os.remove を使用
