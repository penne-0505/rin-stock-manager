from __future__ import annotations

import json

import aiofiles

from utils.paths import DATA_DIR, MAX_BYTES, QUEUE_FILE

# GCで保持する最新の行数
GC_KEEP_LINES = 5000


class FileQueue:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    async def push(self, record: dict) -> None:
        try:
            async with aiofiles.open(QUEUE_FILE, "a") as f:
                await f.write(json.dumps(record) + "\n")
            await self._gc_if_needed()
        except Exception as e:
            raise e

    async def pop_all(self) -> list[dict]:
        if not QUEUE_FILE.exists():
            return []

        items = []
        try:
            async with aiofiles.open(QUEUE_FILE, "r") as f:
                async for line in f:
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

            QUEUE_FILE.unlink(missing_ok=True)
            return items
        except FileNotFoundError:
            return items
        except Exception as e:
            raise e

    async def size(self) -> int:
        try:
            if QUEUE_FILE.exists():
                size = QUEUE_FILE.stat().st_size
                return size
            else:
                return 0
        except Exception:
            return 0

    async def _gc_if_needed(self):
        try:
            current_size = await self.size()
            if current_size <= MAX_BYTES:
                return

            temp_queue_file = QUEUE_FILE.with_suffix(".tmp")
            lines_written = 0
            async with (
                aiofiles.open(QUEUE_FILE, "r") as f_read,
                aiofiles.open(temp_queue_file, "w") as f_write,
            ):
                all_lines = await f_read.readlines()
                lines_to_keep = all_lines[-GC_KEEP_LINES:]
                await f_write.writelines(lines_to_keep)
                lines_written = len(lines_to_keep)

            QUEUE_FILE.unlink()
            temp_queue_file.rename(QUEUE_FILE)

        except FileNotFoundError:
            pass
        except Exception as e:
            if temp_queue_file.exists():
                try:
                    temp_queue_file.unlink()
                except Exception:
                    pass
            raise e
