import asyncio
import logging
from datetime import datetime
from typing import Awaitable, Callable

import aiohttp

logger = logging.getLogger(__name__)


class ReconnectWatcher:
    def __init__(
        self,
        on_reconnect: Callable[[], Awaitable[None]] | None,
        supabase_url: str,
        session_factory: Callable[[], aiohttp.ClientSession] = aiohttp.ClientSession,
        sleep_func: Callable[[float], Awaitable[None]] = asyncio.sleep,
        event_notifier: Callable[[str], None] | None = None,
        ping_interval: int = 5,
    ):
        self._supabase_url = supabase_url.rstrip("/")
        self._running = False
        self._task: asyncio.Task | None = None
        self._fail_count = 0

        self._ping_interval = ping_interval
        self._max_backoff = 60

        self._session_factory = session_factory
        self._sleep = sleep_func
        self._event_notifier = event_notifier

        self._on_reconnects: list[Callable[[], Awaitable[None]]] = []
        if on_reconnect is not None:
            self._on_reconnects.append(on_reconnect)

        self._is_online: bool | None = None
        self._last_checked_at: datetime | None = None

    def register_on_reconnect(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._on_reconnects.append(callback)

    @property
    def is_online(self) -> bool | None:
        return self._is_online

    @property
    def last_checked_at(self) -> datetime | None:
        return self._last_checked_at

    async def _ping(self) -> bool:
        try:
            async with self._session_factory() as session:
                async with session.head(f"{self._supabase_url}/rest/v1/") as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def _watch(self):
        was_offline = False

        try:
            while self._running:
                online = await self._ping()
                self._is_online = online
                self._last_checked_at = datetime.utcnow()

                if online:
                    if was_offline:
                        if self._event_notifier:
                            self._event_notifier("online")
                        for callback in self._on_reconnects:
                            try:
                                await callback()
                            except Exception:
                                pass
                    self._fail_count = 0
                    was_offline = False
                else:
                    self._fail_count += 1
                    if not was_offline:
                        if self._event_notifier:
                            self._event_notifier("offline")
                    was_offline = True

                interval = self._ping_interval * (2 ** (self._fail_count // 3))
                interval = min(interval, self._max_backoff)
                await self._sleep(interval)

        except asyncio.CancelledError:
            pass

        finally:
            pass

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._watch())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
