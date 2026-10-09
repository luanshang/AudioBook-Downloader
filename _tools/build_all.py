#!/usr/bin/env python3
"""一键产出三件套：便携版 ZIP + EXE 安装包 + MSI 安装包。

用法:
    python _tools\build_all.py [--skip-pyinstaller] [--skip-zip] [--skip-exe] [--skip-msi]

前置条件（首次使用需要安装）:
    - Inno Setup 6     -> ISCC.exe   (https://jrsoftware.org/isdl.php)
    - WiX Toolset v4   -> wix.exe    (https://github.com/wixtoolset/wix/releases)

流程:
    1. [可选] python build_release.py  生成便携版目录（若 _release 中不存在）
    2. 便携版 -> Portable.zip
    3. 便携版 -> Inno Setup EXE 安装包
    4. 便携版 -> WiX MSI 安装包
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = ROOT / "Release"
PORTABLE_DIR = RELEASE_DIR / "有声书下载器_便携版"
PORTABLE_EXE = PORTABLE_DIR / "有声书下载器.exe"

APP_NAME = "有声书下载器"
APP_SLUG = "audiobook-downloader"   # GitHub 风格文件名用
APP_VERSION = "2.0.0"

TOOLS = ROOT / "_tools"
ISS_FILE = ROOT / "installer.iss"
WXS_FILE = TOOLS / "app.wxs"
COMPONENTS_WXS = TOOLS / "Components.wxs"

# GitHub 风格发行文件命名: <slug>-<版本>-<类型>.<ext>
OUT_EXE = RELEASE_DIR / f"{APP_SLUG}-v{APP_VERSION}-setup.exe"
OUT_MSI = RELEASE_DIR / f"{APP_SLUG}-v{APP_VERSION}.msi"
OUT_ZIP = RELEASE_DIR / f"{APP_SLUG}-v{APP_VERSION}-portable.zip"

PORTABLE_REL = Path("有声书下载器_便携版")  # zip 内部顶层目录名


def find_tool(names: list[str]) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def ensure_portable() -> None:
    if PORTABLE_EXE.is_file():
        return
    print("便携版不存在，先运行 build_release.py ...")
    subprocess.run([sys.executable, str(ROOT / "build_release.py")], cwd=ROOT, check=True)


def build_zip() -> None:
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    import zipfile
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for file in sorted(PORTABLE_DIR.rglob("*")):
            if file.is_file():
                zf.write(file, str(PORTABLE_DIR.name / file.relative_to(PORTABLE_DIR)))
    print(f"便携版 ZIP: {OUT_ZIP.name}")


def build_exe(iscc: str) -> None:
    print("编译 Inno Setup EXE 安装包 ...")
    subprocess.run([iscc, str(ISS_FILE)], cwd=ROOT, check=True)


def build_msi(wix: str) -> None:
    print("编译 WiX MSI 安装包 ...")
    # 1) harvest 便携版目录 -> Components.wxs
    subprocess.run(
        [wix, "harvest", "dir", str(PORTABLE_DIR),
         "-o", str(COMPONENTS_WXS), "-culture", "zh-CN"],
        cwd=ROOT, check=True,
    )
    # 2) wix build app.wxs Components.wxs -> msi
    subprocess.run(
        [wix, "build", str(WXS_FILE), str(COMPONENTS_WXS),
         "-o", str(OUT_MSI)],
        cwd=ROOT, check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="一键产出便携版ZIP + EXE + MSI 三件套")
    parser.add_argument("--skip-pyinstaller", action="store_true", help="跳过 PyInstaller（需要已有便携版）")
    parser.add_argument("--skip-zip", action="store_true", help="跳过 ZIP")
    parser.add_argument("--skip-exe", action="store_true", help="跳过 EXE")
    parser.add_argument("--skip-msi", action="store_true", help="跳过 MSI")
    args = parser.parse_args()

    if not args.skip_pyinstaller:
        ensure_portable()
    elif not PORTABLE_EXE.is_file():
        print("便携版不存在且跳过 PyInstaller，无法继续。", file=sys.stderr)
        return 1

    if not args.skip_zip:
        build_zip()
    if not args.skip_exe:
        iscc = find_tool(["ISCC.exe", "iscc"])
        if not iscc:
            print("未找到 ISCC.exe，请安装 Inno Setup 6: https://jrsoftware.org/isdl.php", file=sys.stderr)
            return 1
        build_exe(iscc)
    if not args.skip_msi:
        wix = find_tool(["wix.exe", "wix"])
        if not wix:
            print("未找到 wix.exe，请安装 WiX Toolset v4: https://github.com/wixtoolset/wix/releases", file=sys.stderr)
            return 1
        build_msi(wix)

    print("\n打包完成：")
    if not args.skip_zip:
        print(f"  便携版 ZIP : {OUT_ZIP}")
    if not args.skip_exe:
        print(f"  EXE 安装包 : {OUT_EXE}")
    if not args.skip_msi:
        print(f"  MSI 安装包 : {OUT_MSI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
