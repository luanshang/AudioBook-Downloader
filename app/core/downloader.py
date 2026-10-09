# -*- coding: utf-8 -*-
"""
音频下载器
==========
支持：
  - 断点续传（Range 请求 + 临时文件 .part）
  - 进度回调（UI 用）
  - 取消
  - 已存在跳过

实现纯 requests 流式下载，不依赖 Qt，可在 QThread / 任意线程中运行。
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Callable, Optional

import requests

from app.core.logger import get_logger

log = get_logger(__name__)

CHUNK_SIZE = 64 * 1024  # 64KB


class DownloadTask:
    """单文件下载任务。"""

    def __init__(
        self,
        url: str,
        dest: str,
        headers: dict | None = None,
        progress_cb: Optional[Callable[[int, int], None]] = None,
        done_cb: Optional[Callable[[bool, str], None]] = None,
    ):
        self.url = url
        self.dest = dest
        self.headers = headers or {}
        self.progress_cb = progress_cb
        self.done_cb = done_cb
        self._cancel = threading.Event()
        self._downloaded = 0
        self._total = 0

    @property
    def downloaded(self) -> int:
        return self._downloaded

    @property
    def total(self) -> int:
        return self._total

    def cancel(self) -> None:
        self._cancel.set()

    def run(self) -> None:
        """同步执行下载（应放入工作线程）。"""
        dest = Path(self.dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_suffix(dest.suffix + ".part")

        # 断点续传偏移
        offset = 0
        if part.exists():
            offset = part.stat().st_size

        try:
            rng_headers = dict(self.headers)
            if offset > 0:
                rng_headers["Range"] = f"bytes={offset}-"

            with requests.get(self.url, headers=rng_headers, stream=True,
                              timeout=30, allow_redirects=True) as resp:
                resp.raise_for_status()
                total = offset + int(resp.headers.get("Content-Length") or 0)
                self._total = total

                mode = "ab" if offset > 0 else "wb"
                with open(part, mode) as f:
                    for chunk in resp.iter_content(CHUNK_SIZE):
                        if self._cancel.is_set():
                            f.flush()
                            log.info("下载已取消：%s", self.url)
                            self._done(False, "已取消")
                            return
                        if chunk:
                            f.write(chunk)
                            self._downloaded += len(chunk)
                            if self.progress_cb:
                                self.progress_cb(self._downloaded, total)

            # 下载完成：.part -> 正式文件
            if not self._cancel.is_set():
                os.replace(part, dest)
                log.info("下载完成：%s（%d 字节）", dest, self._downloaded)
                self._done(True, dest)
        except Exception as e:
            log.warning("下载失败 [%s] %s -> %s", type(e).__name__, e, self.url)
            self._done(False, str(e))

    def _done(self, ok: bool, msg: str) -> None:
        if self.done_cb:
            try:
                self.done_cb(ok, msg)
            except Exception:
                pass


def download(url: str, dest: str, headers: dict | None = None,
             progress_cb=None, done_cb=None) -> DownloadTask:
    """便捷入口：创建任务并同步执行。"""
    task = DownloadTask(url, dest, headers, progress_cb, done_cb)
    task.run()
    return task


# 便捷：判断文件是否已存在
def exists(dest: str) -> bool:
    return os.path.exists(dest) and os.path.getsize(dest) > 0