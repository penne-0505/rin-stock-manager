from __future__ import annotations

import asyncio  # asyncio をインポート
import json
import logging
import os
from pathlib import Path

import aiofiles
import aiofiles.os as aios

from constants.paths import DATA_DIR
from constants.paths import (
    MAX_BYTES as DEFAULT_MAX_BYTES,
)
from constants.paths import QUEUE_FILE as DEFAULT_QUEUE_FILE

logger = logging.getLogger(__name__)


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
        logger.debug("push: acquiring lock...")
        async with self._lock:  # ロックを取得
            logger.debug("push: lock acquired.")
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
        logger.debug("pop_all: acquiring lock...")
        async with self._lock:  # ロックを取得
            logger.debug("pop_all: lock acquired.")
            if not await aios.path.exists(self.queue_file):
                logger.debug(
                    "pop_all: queue file does not exist, returning empty list."
                )
                logger.debug("pop_all: releasing lock.")
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
                        except json.JSONDecodeError as e:
                            logger.warning(
                                f"キュー内の無効なJSON行をスキップしました: {line.strip()} - {e}"
                            )
                            pass

                await aios.unlink(self.queue_file)
                logger.info(
                    f"{len(items)} 件のアイテムをキューから取り出し、ファイルを削除しました。"
                )
                return items
            except FileNotFoundError:
                logger.info(
                    "pop_all中にキューファイルが見つかりませんでした。空のリストを返します。"
                )
                return []
            except Exception as e:
                logger.error(
                    f"キューからの読み取り中にエラーが発生しました: {e}", exc_info=True
                )
                raise
            finally:
                logger.debug("pop_all: releasing lock.")

    async def size(self) -> int:
        """キューファイルの現在のサイズをバイト単位で返します。"""
        try:
            if await aios.path.exists(self.queue_file):
                stat_result = await aios.stat(self.queue_file)
                return stat_result.st_size
            else:
                return 0
        except Exception as e:
            logger.error(
                f"キューサイズの取得中にエラーが発生しました: {e}", exc_info=True
            )
            return 0

    async def _gc_if_needed(self):
        """キューファイルが最大サイズを超えた場合にガベージコレクションを実行します。"""
        # このメソッドは通常、pushメソッド内のロック下で呼び出される。
        # FileQueue の利用側が _gc_if_needed を直接呼ぶことは想定しないため、
        # push からの呼び出しでロックされていれば十分。
        # テストで直接呼んでいる箇所があるため、堅牢性のためにここでもロックを追加する。
        logger.debug("_gc_if_needed: called (lock should already be held by push).")
        temp_queue_file = self.queue_file.with_suffix(".tmp")
        try:
            current_size = await self.size()  # size() はロックを取得しない
            logger.info(
                f"_gc_if_needed: current_size: {current_size}, self.max_bytes: {self.max_bytes}"
            )
            if current_size <= self.max_bytes:  # self.max_bytes を参照
                logger.info("_gc_if_needed: size is within limit, no GC needed.")
                return
            else:
                logger.info("_gc_if_needed: size EXCEEDS limit, GC will be performed.")

            logger.info(
                f"キューファイルサイズ ({current_size} bytes) が MAX_BYTES ({self.max_bytes} bytes) を超えました。GCを実行します。"
            )

            lines_to_keep_buffer = []
            logger.debug("_gc_if_needed: reading queue file for GC.")
            async with aiofiles.open(
                self.queue_file, "r", encoding="utf-8", newline=""
            ) as f_read:
                all_lines = await f_read.readlines()
                lines_to_keep_buffer = all_lines[-self.GC_KEEP_LINES :]
            logger.debug(f"_gc_if_needed: {len(lines_to_keep_buffer)} lines to keep.")

            logger.debug("_gc_if_needed: writing to temporary GC file.")
            async with aiofiles.open(
                temp_queue_file, "w", encoding="utf-8", newline=""
            ) as f_write:
                for line in lines_to_keep_buffer:
                    await f_write.write(line)

            logger.debug("_gc_if_needed: replacing old queue file with GC'd file.")
            await aios.remove(self.queue_file)
            await aios.rename(temp_queue_file, self.queue_file)
            logger.info(f"GC完了。{len(lines_to_keep_buffer)} 行を保持しました。")

        except FileNotFoundError:
            logger.warning("GC処理中にキューファイルが見つかりませんでした。")
            pass
        except Exception as e:
            logger.error(f"GC処理中にエラーが発生しました: {e}", exc_info=True)
            # raise # ここでraiseすると、push処理全体が失敗する可能性がある。
        finally:
            if await aios.path.exists(temp_queue_file):
                try:
                    await aios.unlink(temp_queue_file)
                    logger.info("一時GCファイルを削除しました。")
                except Exception as e_unlink:
                    logger.error(
                        f"一時GCファイルの削除中にエラーが発生しました: {e_unlink}",
                        exc_info=True,
                    )
