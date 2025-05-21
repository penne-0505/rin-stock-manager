from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import aiofiles
import aiofiles.os as aios

from constants.paths import DATA_DIR
from constants.paths import (
    MAX_BYTES as DEFAULT_MAX_BYTES,
)
from constants.paths import QUEUE_FILE as DEFAULT_QUEUE_FILE


class FileQueue:
    GC_KEEP_LINES = int(os.getenv("QUEUE_GC_KEEP_LINES", "5000"))

    def __init__(
        self, queue_file_path: Path | None = None, max_bytes: int | None = None
    ):  # max_bytes 引数を追加
        if queue_file_path:
            self.queue_file = queue_file_path
        else:
            self.queue_file = DEFAULT_QUEUE_FILE
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()  # asyncio.Lock インスタンスを作成
        self.max_bytes = max_bytes if max_bytes is not None else DEFAULT_MAX_BYTES

    async def push(self, record: dict) -> None:
        """レコードをキューに追加します。"""
        async with self._lock:  # ロックを取得
            try:
                async with aiofiles.open(
                    self.queue_file, "a", encoding="utf-8", newline=""
                ) as f:
                    await f.write(json.dumps(record) + "\n")
                # _gc_if_needed はロック内で呼び出す
                await self._gc_if_needed()
            except Exception:
                # キュー書き込み中のエラー
                pass
            finally:
                # プッシュに成功した場合
                pass

    async def pop_all(self) -> list[dict]:
        """キューからすべてのレコードを取り出します。"""
        async with self._lock:  # ロックを取得
            if not await aios.path.exists(self.queue_file):
                return []
            items = []
            try:
                # newline='' を追加 (読み取り時も念のため)
                async with aiofiles.open(
                    self.queue_file, "r", encoding="utf-8", newline=""
                ) as f:
                    async for line in f:
                        try:
                            items.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

                await aios.unlink(self.queue_file)
                return items
            except FileNotFoundError:
                return []
            except Exception:
                raise
            finally:
                pass

    async def size(self) -> int:
        """キューファイルの現在のサイズをバイト単位で返します。"""
        try:
            if await aios.path.exists(self.queue_file):
                stat_result = await aios.stat(self.queue_file)
                return stat_result.st_size
            else:
                return 0
        except Exception:
            return 0

    async def _gc_if_needed(self):
        """キューファイルが最大サイズを超えた場合にガベージコレクションを実行します。"""
        temp_queue_file = self.queue_file.with_suffix(".tmp")
        try:
            current_size = await self.size()  # size() はロックを取得しない
            if current_size <= self.max_bytes:  # self.max_bytes を参照
                return
            else:
                pass

            lines_to_keep_buffer = []
            async with aiofiles.open(
                self.queue_file, "r", encoding="utf-8", newline=""
            ) as f_read:
                all_lines = await f_read.readlines()
                lines_to_keep_buffer = all_lines[-self.GC_KEEP_LINES :]

            async with aiofiles.open(
                temp_queue_file, "w", encoding="utf-8", newline=""
            ) as f_write:
                for line in lines_to_keep_buffer:
                    await f_write.write(line)

            await aios.remove(self.queue_file)
            await aios.rename(temp_queue_file, self.queue_file)

        except FileNotFoundError:
            pass
        except Exception:
            pass
        finally:
            if await aios.path.exists(temp_queue_file):
                try:
                    await aios.unlink(temp_queue_file)
                except Exception:
                    pass
