from unittest.mock import AsyncMock, MagicMock

from src.services.reconnect_watcher import ReconnectWatcher


async def test_ping_success(mocker):
    """_pingが成功するケースをテストします。"""
    mock_datetime = mocker.patch("src.services.reconnect_watcher.datetime")
    mock_utcnow = MagicMock()
    mock_datetime.utcnow = mock_utcnow

    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_session.head.return_value.__aenter__.return_value = mock_response
    mock_session_factory = MagicMock(return_value=mock_session)

    watcher = ReconnectWatcher(
        on_reconnect=None,
        supabase_url="http://test.supabase.co",
        session_factory=mock_session_factory,
    )  # 閉じ括弧を追加

    result = await watcher._ping()
    assert result is True
    mock_session_factory.assert_called_once()
    mock_session.head.assert_called_once_with("http://test.supabase.co/rest/v1/")


async def test_ping_failure_status_code(mocker):
    """_pingがステータスコードにより失敗するケースをテストします。"""
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 500  # 200以外
    mock_session.head.return_value.__aenter__.return_value = mock_response
    mock_session_factory = MagicMock(return_value=mock_session)

    watcher = ReconnectWatcher(
        on_reconnect=None,
        supabase_url="http://test.supabase.co",
        session_factory=mock_session_factory,
    )  # 閉じ括弧を追加
    result = await watcher._ping()
    assert result is False


async def test_ping_failure_exception(mocker):
    """_pingが例外により失敗するケースをテストします。"""
    mock_session = AsyncMock()
    mock_session.head.side_effect = Exception("Test Exception")
    mock_session_factory = MagicMock(return_value=mock_session)

    watcher = ReconnectWatcher(
        on_reconnect=None,
        supabase_url="http://test.supabase.co",
        session_factory=mock_session_factory,
    )  # 閉じ括弧を追加
    result = await watcher._ping()
    assert result is False
