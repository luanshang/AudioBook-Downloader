# -*- coding: utf-8 -*-
"""
音频格式转换器
==============
M4A -> MP3 批量转换（调用 ffmpeg）。

与原 aardio 版一致：
  - 输出音质：低 96k / 中 128k / 高 192k / 超高 320k
  - 跳过已存在的目标文件
  - 支持倍速（原版 UI 有选项，转码时以 atempo 实现）
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

# 音质 -> ffmpeg 码率
BITRATES = {
    "低音质": "96k",
    "中音质": "128k",
    "高音质": "192k",
    "超高音质": "320k",
}
DEFAULT_QUALITY = "高音质"

# 倍速 -> atempo 参数
SPEEDS = {
    "0.5倍": "0.5",
    "0.8倍": "0.8",
    "1.0倍": "1.0",
    "1.25倍": "1.25",
    "1.5倍": "1.5",
    "2.0倍": "2.0",
}
DEFAULT_SPEED = "1.0倍"


class Converter:
    """ffmpeg 音频格式转换器。"""

    def __init__(self, quality: str = DEFAULT_QUALITY, speed: str = DEFAULT_SPEED,
                 ffmpeg_path: str = "ffmpeg"):
        self.bitrate = BITRATES.get(quality, BITRATES[DEFAULT_QUALITY])
        self.speed = SPEEDS.get(speed, "1.0")
        self.ffmpeg_path = self._resolve_ffmpeg(ffmpeg_path)

    @staticmethod
    def _resolve_ffmpeg(path: str) -> str:
        """若未提供系统 ffmpeg，检查内置目录。"""
        if path and path != "ffmpeg":
            return path
        if shutil.which("ffmpeg"):
            return "ffmpeg"
        # 程序内置目录
        local = Path(__file__).resolve().parent.parent / "resources" / "ffmpeg.exe"
        return str(local) if local.exists() else "ffmpeg"

    def find_m4a(self, folder: str) -> list[str]:
        """列出目录下全部 .m4a / .m4b / .aac 文件。"""
        folder = Path(folder)
        files = []
        for ext in ("*.m4a", "*.m4b", "*.aac"):
            files.extend(str(p) for p in folder.glob(ext))
        return sorted(files)

    def convert_file(self, src: str, out_dir: str | None = None,
                     progress_cb: Optional[Callable[[str], None]] = None) -> str:
        """
        转换单文件。

        Returns: 目标文件路径
        """
        src = Path(src)
        # ffmpeg 需要扩展名匹配容器，M4A 转 MP3
        target = Path(out_dir or src.parent) / (src.stem + ".mp3")

        if target.exists() and target.stat().st_size > 0:
            if progress_cb:
                progress_cb(f"跳过 {src.name}（已存在）")
            return str(target)

        cmd = [self.ffmpeg_path, "-y", "-i", str(src)]
        if self.speed != "1.0":
            status = f"atempo={self.speed}"
            if float(self.speed) > 2.0:
                # ffmpeg atempo 上限 2.0，用串接
                status = f"atempo=2.0,atempo={float(self.speed) / 2.0:.2f}"
            cmd += ["-af", status]
        cmd += ["-b:a", self.bitrate, "-vn", str(target)]

        if progress_cb:
            progress_cb(f"转换中 {src.name} ...")
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg 转换失败: {result.stderr[-500:]}")

        if progress_cb:
            progress_cb(f"完成 {target.name}")
        return str(target)

    def convert_folder(self, folder: str, progress_cb=None) -> tuple[int, int]:
        """
        批量转换目录下全部 M4A。

        Returns: (成功数, 跳过数)
        """
        files = self.find_m4a(folder)
        ok, skipped = 0, 0
        for f in files:
            target = Path(f).with_suffix(".mp3")
            if target.exists() and target.stat().st_size > 0:
                skipped += 1
                if progress_cb:
                    progress_cb(f"跳过 {Path(f).name}")
                continue
            try:
                self.convert_file(f, progress_cb=progress_cb)
                ok += 1
            except Exception as e:
                if progress_cb:
                    progress_cb(f"失败 {Path(f).name}: {e}")
        return ok, skipped


if __name__ == "__main__":
    c = Converter()
    print("ffmpeg:", c.ffmpeg_path)
    print("码率:", c.bitrate, "倍速:", c.speed)