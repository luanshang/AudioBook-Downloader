#!/usr/bin/env python3
"""打包便携版 ZIP：将 build/output/有声书下载器_便携版 压缩为 ZIP。

用法:
    uv run python build/packaging/make_portable_zip.py
产物:
    build/output/有声书下载器_便携版_v0.0.1.zip   （zip 内顶层目录为 有声书下载器_便携版/，
                                              解压后双击 有声书下载器.exe 即可启动）
"""

from __future__ import annotations

import os
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RELEASE_DIR = ROOT / "build" / "output"
PORTABLE_DIR = RELEASE_DIR / "有声书下载器_便携版"
APP_NAME = "有声书下载器"
APP_VERSION = "0.0.1"
OUT_ZIP = RELEASE_DIR / f"{APP_NAME}_便携版_v{APP_VERSION}.zip"


def build_zip() -> None:
    if not PORTABLE_DIR.is_dir():
        print(f"便携版目录不存在: {PORTABLE_DIR}", file=sys.stderr)
        print("请先运行 uv run python build/scripts/build_release.py 生成便携版。", file=sys.stderr)
        raise SystemExit(1)

    if OUT_ZIP.exists():
        OUT_ZIP.unlink()

    total_files = sum(1 for _ in PORTABLE_DIR.rglob("*") if _.is_file())
    print(f"正在压缩 {total_files} 个文件 -> {OUT_ZIP} ...")

    # ZIP64 自动启用（>4GB 或 >65535 文件会自动切 ZIP64，标准解压工具均支持）
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for file in sorted(PORTABLE_DIR.rglob("*")):
            if not file.is_file():
                continue
            # zip 内路径: 有声书下载器_便携版/<相对路径>，顶层保留目录名
            arcname = str(PORTABLE_DIR.name / file.relative_to(PORTABLE_DIR))
            zf.write(file, arcname)

    size_mb = round(OUT_ZIP.stat().st_size / 1024 / 1024, 1)
    print(f"完成: {OUT_ZIP.name} ({size_mb} MB)")


if __name__ == "__main__":
    build_zip()
