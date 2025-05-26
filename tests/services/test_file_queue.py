import asyncio
import json
from pathlib import Path

import aiofiles
import pytest
import pytest_asyncio

from src.services.file_queue import FileQueue

# pytest-asyncio が 'auto' モードで実行されるようにする
# pytest.ini または pyproject.toml で設定することも可能
pytest_plugins = ("pytest_asyncio",)


@pytest_asyncio.fixture
async def queue(tmp_path: Path):  # monkeypatch を削除
    """テスト用のFileQueueインスタンスと一時的なキューファイルパスを提供するフィクスチャ"""
    test_queue_file = tmp_path / "test_queue.jsonl"
    # DATA_DIR は FileQueue 内でデフォルト値が使われるか、
    # 必要であれば queue_file_path と同様にコンストラクタで渡すように FileQueue を変更することも検討
    # ここでは DATA_DIR のモンキーパッチは削除し、FileQueue のデフォルト挙動に任せるか、
    # FileQueue 側で queue_file_path.parent を使うように変更したため、
    # test_data_dir の設定は不要になる。

    # FileQueueインスタンスを作成し、テスト用のファイルパスを渡す
    q = FileQueue(queue_file_path=test_queue_file)
    # テスト終了時にキューファイルをクリーンアップ
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


@pytest.mark.asyncio
async def test_gc_not_needed(queue: FileQueue, monkeypatch):
    """GCが不要な場合のテスト (MAX_BYTES以内)"""
    # monkeypatch.setattr("src.utils.paths.MAX_BYTES", 1024)  # 十分大きな値に設定 # 変更
    queue.max_bytes = 1024  # インスタンスの属性を直接変更
    monkeypatch.setattr(queue, "GC_KEEP_LINES", 1)

    record = {"id": 1, "data": "small_data"}
    await queue.push(record)

    initial_size = await queue.size()
    await queue._gc_if_needed()  # 明示的に呼び出す
    size_after_gc = await queue.size()

    assert size_after_gc == initial_size  # サイズは変わらないはず
    items = await queue.pop_all()
    assert len(items) == 1  # レコードは残っている


@pytest.mark.asyncio
async def test_gc_triggered_and_keeps_lines(queue: FileQueue, monkeypatch, tmp_path):
    """GCがトリガーされ、指定された行数を保持するテスト"""
    # MAX_BYTES を小さく設定してGCを強制する
    # 3レコード書き込むが、2レコード分のサイズより小さく、1レコード分のサイズより大きくする
    record1 = {"id": 1, "data": "record_data_1"}
    record2 = {"id": 2, "data": "record_data_2"}
    record3 = {"id": 3, "data": "record_data_3"}

    record1_line = json.dumps(record1) + "\n"
    record2_line = json.dumps(record2) + "\n"
    record3_line = json.dumps(record3) + "\n"

    # MAX_BYTES を (record1 + record2 のサイズ) - 1 に設定
    # これにより、3レコード目を書き込んだ後にGCがトリガーされる
    max_bytes_limit = (
        len(record1_line.encode("utf-8")) + len(record2_line.encode("utf-8")) - 1
    )
    # monkeypatch.setattr("src.utils.paths.MAX_BYTES", max_bytes_limit) # 変更
    queue.max_bytes = max_bytes_limit  # インスタンスの属性を直接変更

    # GCで保持する行数を2に設定
    gc_keep_lines = 2
    monkeypatch.setattr(queue, "GC_KEEP_LINES", gc_keep_lines)

    # 1. 最初のレコードを書き込む (GCはトリガーされない)
    await queue.push(record1)
    assert await queue.size() == len(record1_line.encode("utf-8"))

    # 2. 2番目のレコードを書き込む (GCはトリガーされない)
    await queue.push(record2)
    current_size = await queue.size()
    assert current_size == len(record1_line.encode("utf-8")) + len(
        record2_line.encode("utf-8")
    )
    assert (
        current_size > max_bytes_limit
    )  # この時点でMAX_BYTESを超えているが、push内のgc_if_neededは次のpushで評価

    # 3. 3番目のレコードを書き込む (ここでGCがトリガーされるはず)
    await queue.push(record3)  # このpushの中で_gc_if_neededが呼ばれる

    # GC後のファイルサイズを確認
    # record2 と record3 が残るはず
    expected_size_after_gc = len(record2_line.encode("utf-8")) + len(
        record3_line.encode("utf-8")
    )
    size_after_gc = await queue.size()
    assert size_after_gc == expected_size_after_gc

    # GC後に保持されているレコードを確認
    items = await queue.pop_all()
    assert len(items) == gc_keep_lines
    assert items[0] == record2  # 古いrecord1は削除され、record2が最初に来る
    assert items[1] == record3


@pytest.mark.asyncio
async def test_pop_all_with_invalid_json_lines(queue: FileQueue, tmp_path):
    """不正なJSON行が含まれる場合のpop_allのテスト"""
    valid_record1 = {"id": 1, "data": "valid_1"}
    valid_record2 = {"id": 2, "data": "valid_2"}
    invalid_line = "this is not a json line\n"

    # 手動でファイルに書き込む
    queue_file_path = queue.queue_file  # queue.QUEUE_FILE を queue.queue_file に変更
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
async def test_gc_with_empty_file_after_exceeding_max_bytes(
    queue: FileQueue, monkeypatch
):
    """MAX_BYTESを超えた後、ファイルが空（またはGC対象行がない）場合のGCテスト"""
    # monkeypatch.setattr("src.utils.paths.MAX_BYTES", 10)  # 非常に小さい値 # 変更
    queue.max_bytes = 10  # インスタンスの属性を直接変更
    monkeypatch.setattr(queue, "GC_KEEP_LINES", 5)

    # MAX_BYTES を超えるデータを書き込む
    await queue.push({"id": 1, "data": "some data that exceeds max bytes"})
    # この時点でGCが実行され、ファイルが空になるか、または指定行数保持しようとするが元が1行なので1行残る

    # 再度GCを試みる（例えば、pop_allの後など、ファイルが存在しない状態で呼ばれるケースを模倣）
    # _gc_if_needed はファイルが存在しない場合、またはサイズが小さければ何もしない
    # ここでは、push後のGCでファイルが小さくなっている（または空）状態を想定
    await queue._gc_if_needed()

    assert await queue.size() <= len(
        json.dumps({"id": 1, "data": "some data that exceeds max bytes"}).encode()
        + b"\n"
    )
    # エラーが発生しないことを確認

    items = await queue.pop_all()
    # GC_KEEP_LINESが5でも、元の行数が1なので1件のはず
    assert len(items) == 1


@pytest.mark.asyncio
async def test_concurrent_push_and_pop(tmp_path, monkeypatch):
    """複数のコルーチンからの同時pushとpop_allのテスト（基本的な競合状態の確認）"""
    # このテストは FileQueue の基本的なスレッドセーフティや
    # asyncio のロック機構に依存する部分を厳密にテストするものではなく、
    # 通常の利用シーンでの基本的な動作確認を目的とします。
    # より厳密な競合テストは複雑なセットアップが必要になります。

    test_queue_file = tmp_path / "concurrent_queue.jsonl"
    # monkeypatch.setattr("src.utils.paths.QUEUE_FILE", test_queue_file) # 削除
    # test_data_dir = tmp_path / "data_concurrent" # 削除
    # monkeypatch.setattr("src.utils.paths.DATA_DIR", test_data_dir) # 削除

    queue_instance = FileQueue(
        queue_file_path=test_queue_file
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

    # 全てのpushが終わった後にpop_all
    all_items = await queue_instance.pop_all()

    assert len(all_items) == total_records
    # IDが一意であることを確認 (順序は保証されない場合があるためセットで比較)
    assert len(set(item["id"] for item in all_items)) == total_records

    # クリーンアップ
    if await aiofiles.os.path.exists(test_queue_file):  # aiofiles.os.path.exists を使用
        await aiofiles.os.remove(test_queue_file)  # aiofiles.os.remove を使用
