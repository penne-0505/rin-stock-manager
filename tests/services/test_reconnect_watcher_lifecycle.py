import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.reconnect_watcher import ReconnectWatcher


async def test_start_stop_cycle(mocker):
    """startとstopがタスクを正しく管理するかテストします。"""
    watcher = ReconnectWatcher(None, "http://test.url")

    # _watch が無限ループしないようにモック化
    mock_watch_method = AsyncMock()
    mocker.patch.object(watcher, "_watch", new=mock_watch_method)

    watcher.start()
    assert watcher._running is True
    assert watcher._task is not None
    # _watch は create_task で起動される
    # watcher._watch が呼び出されるのを待つ
    await asyncio.sleep(0.01)  # タスクがスケジュールされるのを少し待つ
    mock_watch_method.assert_called_once()

    await watcher.stop()
    assert watcher._running is False
    # _watch モックがキャンセルされたことを確認
    assert mock_watch_method.cancelled() is True


async def test_watch_online_to_offline_and_back_to_online(mocker):
    """オンライン -> オフライン -> オンラインの遷移をテストします。"""
    mock_datetime = mocker.patch("src.services.reconnect_watcher.datetime")
    fixed_time = MagicMock()
    mock_datetime.utcnow.return_value = fixed_time

    mock_on_reconnect = AsyncMock()
    mock_event_notifier = MagicMock()
    mock_sleep = AsyncMock()

    # _ping の戻り値を制御するためのリスト
    ping_results = [True, False, False, True]
    ping_call_count = 0

    async def mock_ping_sequence():
        nonlocal ping_call_count
        ping_call_count += 1
        if not ping_results:
            return False
        return ping_results.pop(0)

    watcher = ReconnectWatcher(
        on_reconnect=mock_on_reconnect,
        supabase_url="http://test.url",
        sleep_func=mock_sleep,
        event_notifier=mock_event_notifier,
        ping_interval=0.01,  # テスト時間を短縮
    )
    watcher._ping = AsyncMock(side_effect=mock_ping_sequence)

    watcher.start()
    await asyncio.sleep(0.001)  # _watch が開始されるのを待つ

    ping_call_count_target = 4  # ping_results の元の要素数
    try:

        async def wait_for_pings_or_completion():
            # ping_call_count がターゲットに達するか、タスクが完了するまで待つ
            while ping_call_count < ping_call_count_target and not (
                watcher._task and watcher._task.done()
            ):
                await asyncio.sleep(0.005)

        await asyncio.wait_for(wait_for_pings_or_completion(), timeout=1.0)

    except asyncio.TimeoutError:
        pass

    await watcher.stop()

    assert ping_call_count == ping_call_count_target

    mock_event_notifier.assert_any_call("offline")
    mock_event_notifier.assert_any_call("online")
    mock_on_reconnect.assert_called_once()

    assert watcher.is_online is True
    assert watcher.last_checked_at == fixed_time
    assert watcher._fail_count == 0

    assert mock_sleep.call_count >= 3
    expected_intervals = [
        watcher._ping_interval,
        watcher._ping_interval * (2 ** (1 // 3)),
        watcher._ping_interval * (2 ** (2 // 3)),
    ]
    for i, call_args in enumerate(mock_sleep.call_args_list[:3]):
        assert abs(call_args[0][0] - expected_intervals[i]) < 0.001


async def test_multiple_on_reconnect_callbacks(mocker):
    """複数のon_reconnectコールバックが呼ばれるかテストします。"""
    mock_datetime = mocker.patch("src.services.reconnect_watcher.datetime")
    fixed_time = MagicMock()
    mock_datetime.utcnow.return_value = fixed_time

    callback1 = AsyncMock()
    callback2 = AsyncMock()
    mock_event_notifier = MagicMock()
    mock_sleep = AsyncMock()

    ping_results = [False, True]
    ping_call_count = 0

    async def mock_ping_sequence():
        nonlocal ping_call_count
        ping_call_count += 1
        if not ping_results:
            if watcher._running:
                watcher._running = False
            return False
        return ping_results.pop(0)

    watcher = ReconnectWatcher(
        on_reconnect=callback1,
        supabase_url="http://test.url",
        sleep_func=mock_sleep,
        event_notifier=mock_event_notifier,
        ping_interval=0.01,
    )
    watcher.register_on_reconnect(callback2)
    watcher._ping = AsyncMock(side_effect=mock_ping_sequence)

    watcher.start()
    try:
        await asyncio.wait_for(watcher._task, timeout=0.5)
    except asyncio.TimeoutError:
        if watcher._task and not watcher._task.done():
            await watcher.stop()
        pytest.fail("Watcher task did not complete in time")
    except asyncio.CancelledError:
        pass

    callback1.assert_called_once()
    callback2.assert_called_once()
    mock_event_notifier.assert_any_call("offline")
    mock_event_notifier.assert_any_call("online")
