from unittest.mock import AsyncMock, MagicMock

from src.services.reconnect_watcher import ReconnectWatcher


async def test_initialization(mocker):
    """初期化が正しく行われるかテストします。"""
    mock_on_reconnect = AsyncMock()
    mock_session_factory = MagicMock()
    mock_sleep = AsyncMock()
    mock_event_notifier = MagicMock()

    watcher = ReconnectWatcher(
        on_reconnect=mock_on_reconnect,
        supabase_url="http://test.supabase.co",
        session_factory=mock_session_factory,
        sleep_func=mock_sleep,
        event_notifier=mock_event_notifier,
        ping_interval=1,
    )

    assert watcher._supabase_url == "http://test.supabase.co"
    assert mock_on_reconnect in watcher._on_reconnects
    assert watcher._session_factory == mock_session_factory
    assert watcher._sleep == mock_sleep
    assert watcher._event_notifier == mock_event_notifier
    assert watcher._ping_interval == 1
    assert watcher.is_online is None
    assert watcher.last_checked_at is None


async def test_register_on_reconnect():
    """register_on_reconnect でコールバックが追加されるかテストします。"""
    watcher = ReconnectWatcher(None, "http://test.url")
    assert len(watcher._on_reconnects) == 0

    callback1 = AsyncMock()
    watcher.register_on_reconnect(callback1)
    assert callback1 in watcher._on_reconnects

    callback2 = AsyncMock()
    watcher.register_on_reconnect(callback2)
    assert callback2 in watcher._on_reconnects
    assert len(watcher._on_reconnects) == 2
