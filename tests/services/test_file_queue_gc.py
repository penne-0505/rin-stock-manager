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
    test_queue_file = tmp_path / "test_queue_gc.jsonl"  # ファイル名を変更
    # monkeypatch.setattr("src.utils.paths.QUEUE_FILE", test_queue_file) # 削除
    # test_data_dir = tmp_path / "data_gc"  # ディレクトリ名も変更 # 削除
    # monkeypatch.setattr("src.utils.paths.DATA_DIR", test_data_dir) # 削除

    q = FileQueue(queue_file_path=test_queue_file)  # コンストラクタでパスを指定
    yield q
    # aiofiles.os を使用して非同期的にファイル操作を行う
    if await aiofiles.os.path.exists(test_queue_file):
        await aiofiles.os.remove(test_queue_file)
    # GCによって作成される可能性のある一時ファイルも削除
    temp_gc_file = test_queue_file.with_suffix(".tmp")
    if await aiofiles.os.path.exists(temp_gc_file):  # aiofiles.os.path.exists を使用
        await aiofiles.os.remove(temp_gc_file)  # aiofiles.os.remove を使用


@pytest.mark.asyncio
async def test_gc_not_needed(queue: FileQueue, monkeypatch):
    """GCが不要な場合のテスト (MAX_BYTES以内)"""
    # monkeypatch.setattr("src.utils.paths.MAX_BYTES", 1024) # 修正: インスタンスの属性を直接変更
    monkeypatch.setattr(queue, "max_bytes", 1024)
    print("\n[test_gc_not_needed] monkeypatched queue.max_bytes to 1024")
    print(f"[test_gc_not_needed] queue.max_bytes BEFORE push: {queue.max_bytes}")
    monkeypatch.setattr(queue, "GC_KEEP_LINES", 1)

    record = {"id": 1, "data": "small_data"}
    await queue.push(record)

    initial_size = await queue.size()
    print(f"[test_gc_not_needed] initial_size: {initial_size}")
    print("[test_gc_not_needed] Calling queue._gc_if_needed() explicitly...")
    await queue._gc_if_needed()  # 明示的に呼び出す
    size_after_gc = await queue.size()
    print(f"[test_gc_not_needed] size_after_gc: {size_after_gc}")

    assert size_after_gc == initial_size  # サイズは変わらないはず
    items = await queue.pop_all()
    assert len(items) == 1  # レコードは残っている


@pytest.mark.asyncio
async def test_gc_triggered_and_keeps_lines(queue: FileQueue, monkeypatch):
    """GCがトリガーされ、指定された行数を保持するテスト"""
    record1 = {"id": 1, "data": "record_data_1"}
    record2 = {"id": 2, "data": "record_data_2"}
    record3 = {"id": 3, "data": "record_data_3"}

    record1_line = json.dumps(record1) + "\n"
    record2_line = json.dumps(record2) + "\n"
    record3_line = json.dumps(record3) + "\n"

    max_bytes_limit = (
        len(record1_line.encode("utf-8")) + len(record2_line.encode("utf-8")) - 1
    )
    # monkeypatch.setattr("src.utils.paths.MAX_BYTES", max_bytes_limit) # 修正: インスタンスの属性を直接変更
    monkeypatch.setattr(queue, "max_bytes", max_bytes_limit)
    print(
        f"\n[test_gc_triggered_and_keeps_lines] monkeypatched queue.max_bytes to {max_bytes_limit}"
    )
    print(
        f"[test_gc_triggered_and_keeps_lines] queue.max_bytes BEFORE pushes: {queue.max_bytes}"
    )

    gc_keep_lines = 2
    monkeypatch.setattr(queue, "GC_KEEP_LINES", gc_keep_lines)

    await queue.push(record1)
    await queue.push(record2)
    await queue.push(record3)  # このpushの中で_gc_if_neededが呼ばれる

    expected_size_after_gc = len(record2_line.encode("utf-8")) + len(
        record3_line.encode("utf-8")
    )
    size_after_gc = await queue.size()
    print(
        f"[test_gc_triggered_and_keeps_lines] expected_size_after_gc: {expected_size_after_gc}"
    )
    print(f"[test_gc_triggered_and_keeps_lines] size_after_gc: {size_after_gc}")
    assert size_after_gc == expected_size_after_gc

    items = await queue.pop_all()
    assert len(items) == gc_keep_lines
    assert items[0] == record2
    assert items[1] == record3


@pytest.mark.asyncio
async def test_gc_with_empty_file_after_exceeding_max_bytes(
    queue: FileQueue, monkeypatch
):
    """MAX_BYTESを超えた後、ファイルが空（またはGC対象行がない）場合のGCテスト"""
    # monkeypatch.setattr("src.utils.paths.MAX_BYTES", 10) # 修正: インスタンスの属性を直接変更
    monkeypatch.setattr(queue, "max_bytes", 10)
    print(
        "\n[test_gc_with_empty_file_after_exceeding_max_bytes] monkeypatched queue.max_bytes to 10"
    )
    print(
        f"[test_gc_with_empty_file_after_exceeding_max_bytes] queue.max_bytes BEFORE push: {queue.max_bytes}"
    )
    monkeypatch.setattr(queue, "GC_KEEP_LINES", 5)

    record_content = {"id": 1, "data": "some data that exceeds max bytes"}
    await queue.push(record_content)
    # この時点でGCが実行され、ファイルが空になるか、または指定行数保持しようとするが元が1行なので1行残る

    await queue._gc_if_needed()  # 再度GCを試みる

    # GC後、1行だけ残るはず
    expected_size = len(json.dumps(record_content).encode("utf-8") + b"\n")
    current_size = await queue.size()
    print(
        f"[test_gc_with_empty_file_after_exceeding_max_bytes] expected_size: {expected_size}"
    )
    print(
        f"[test_gc_with_empty_file_after_exceeding_max_bytes] current_size: {current_size}"
    )

    # GC_KEEP_LINES が5でも、元の行数が1なので、1行残るか、あるいは0になる（実装による）
    # FileQueueの実装では、元の行数 < GC_KEEP_LINES の場合、元の行数だけ残す
    assert current_size == expected_size

    items = await queue.pop_all()
    assert len(items) == 1
    assert items[0] == record_content
