#!/usr/bin/env python3
r"""一键产出三件套：便携版 ZIP + EXE 安装包 + MSI 安装包。

用法:
    uv run python build\packaging\build_all.py [--skip-pyinstaller] [--skip-zip] [--skip-exe] [--skip-msi]

前置条件（首次使用需要安装）:
    - Inno Setup 6     -> ISCC.exe   (https://jrsoftware.org/isdl.php)
    - WiX Toolset v4   -> wix.exe    (https://github.com/wixtoolset/wix/releases)

流程:
    1. [可选] python build\scripts\build_release.py  生成便携版目录（若 build/output 中不存在）
    2. 便携版 -> Portable.zip
    3. 便携版 -> Inno Setup EXE 安装包
    4. 便携版 -> WiX MSI 安装包
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RELEASE_DIR = ROOT / "build" / "output"
PORTABLE_DIR = RELEASE_DIR / "有声书下载器_便携版"
PORTABLE_EXE = PORTABLE_DIR / "有声书下载器.exe"

APP_NAME = "有声书下载器"
APP_SLUG = "AudioBook Downloader"   # 发行文件名中的 slug
APP_VERSION = "0.0.1"


def configure_version(version: str) -> None:
    global APP_VERSION, OUT_EXE, OUT_MSI, OUT_ZIP
    APP_VERSION = version
    OUT_EXE = RELEASE_DIR / f"{APP_SLUG}-v{APP_VERSION}-setup.exe"
    OUT_MSI = RELEASE_DIR / f"{APP_SLUG}-v{APP_VERSION}.msi"
    OUT_ZIP = RELEASE_DIR / f"{APP_SLUG}-v{APP_VERSION}-portable.zip"

TOOLS = ROOT / "build" / "packaging"
ISS_FILE = TOOLS / "installer.iss"
WXS_FILE = TOOLS / "app.wxs"
COMPONENTS_WXS = TOOLS / "Components.wxs"

# GitHub 风格发行文件命名: <slug>-<版本>-<类型>.<ext>
OUT_EXE = RELEASE_DIR / f"{APP_SLUG}-v{APP_VERSION}-setup.exe"
OUT_MSI = RELEASE_DIR / f"{APP_SLUG}-v{APP_VERSION}.msi"
OUT_ZIP = RELEASE_DIR / f"{APP_SLUG}-v{APP_VERSION}-portable.zip"

PORTABLE_REL = Path(f"{APP_SLUG}-v{APP_VERSION}-portable")  # zip 内部顶层目录名（与 ZIP 文件名一致）


def find_tool(names: list[str], fallback_dirs: list[Path]) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    for d in fallback_dirs:
        candidate = d
        if candidate.is_file():
            return str(candidate)
    return None


ISCC_FALLBACKS = [
    Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
    Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    Path(r"C:\Program Files\Inno Setup 7\ISCC.exe"),
    Path(r"C:\Program Files (x86)\Inno Setup 7\ISCC.exe"),
]
WIX_FALLBACKS = [
    Path(r"C:\Program Files\WiX Toolset v4\bin\wix.exe"),
    Path(r"C:\Program Files (x86)\WiX Toolset v4\bin\wix.exe"),
    Path(r"C:\Program Files\WiX Toolset v7.0\bin\wix.exe"),
    Path(r"C:\Program Files (x86)\WiX Toolset v7.0\bin\wix.exe"),
    Path(r"C:\Program Files\WiX Toolset v7\bin\wix.exe"),
    Path(r"C:\Program Files (x86)\WiX Toolset v7\bin\wix.exe"),
]


def ensure_portable() -> None:
    if PORTABLE_EXE.is_file():
        return
    print("便携版不存在，先运行 build_release.py ...")
    subprocess.run([sys.executable, str(ROOT / "build" / "scripts" / "build_release.py")], cwd=ROOT, check=True)


def build_zip() -> None:
    if not PORTABLE_DIR.is_dir():
        raise FileNotFoundError(f"便携版目录不存在: {PORTABLE_DIR}")
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    import zipfile
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for file in sorted(PORTABLE_DIR.rglob("*")):
            if file.is_file():
                zf.write(file, str(PORTABLE_REL / file.relative_to(PORTABLE_DIR)))
    print(f"便携版 ZIP: {OUT_ZIP.name}")


def build_exe(iscc: str) -> None:
    print("编译 Inno Setup EXE 安装包 ...")
    subprocess.run([iscc, f"/DMyAppVersion={APP_VERSION}", str(ISS_FILE)], cwd=ROOT, check=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_latest_manifest() -> None:
    """写出供更新检查使用的最新发行清单。"""
    files = []
    for path, kind in ((OUT_EXE, "installer"), (OUT_MSI, "msi"), (OUT_ZIP, "portable")):
        if not path.is_file():
            continue
        files.append({
            "name": path.name,
            "type": kind,
            "url": path.name,
            "size": path.stat().st_size,
            "sha256": _sha256(path),
        })
    manifest = {
        "name": APP_NAME,
        "version": APP_VERSION,
        "tag": f"v{APP_VERSION}",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }
    target = RELEASE_DIR / "latest.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  更新清单 : {target}")


def _wix_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _sane_id(value: str, prefix: str, used: set[str]) -> str:
    """生成合法 WiX 标识符并保证唯一。

    WiX 标识符只允许：ASCII 字母 a-z/A-Z、数字 0-9、下划线 _、句点 .，
    且必须以字母或下划线开头，最长 72 字符。连字符、中文等一律替换为下划线。
    """
    import hashlib
    base = "".join(
        c if (c.isascii() and (c.isalnum() or c in "_.")) else "_" for c in value
    )
    if not base or (not base[0].isalpha() and base[0] != "_"):
        base = prefix + "_" + base
    if len(base) > 70:
        digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
        base = base[:59] + "_" + digest
    candidate = base
    n = 1
    while candidate in used:
        n += 1
        candidate = f"{base}_{n}"
    used.add(candidate)
    return candidate


def generate_components_wxs(output: Path) -> None:
    """用 Python 遍历便携版目录生成 Components.wxs（含完整目录树）。

    WiX v7 移除了 harvest 子命令，这里每个文件一个 Component（KeyPath=yes），
    目录结构用嵌套 Directory 表达，组件放在 INSTALLFOLDER 下。
    """
    print(f"生成组件定义: {output.name}")
    used_ids: set[str] = set()
    component_refs: list[str] = []

    def emit_dir(dir_path: Path, dir_id: str, indent: int) -> list[str]:
        pad = "  " * indent
        lines = [f'{pad}<Directory Id="{dir_id}" Name="{_wix_escape(dir_path.name)}">']
        for entry in sorted(dir_path.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_dir():
                sub_id = _sane_id(entry.name, "dir", used_ids)
                lines.extend(emit_dir(entry, sub_id, indent + 1))
            elif entry.is_file():
                comp_id = _sane_id(entry.name, "cmp", used_ids)
                file_id = _sane_id(entry.name, "fil", used_ids)
                lines.append(
                    f'{pad}  <Component Id="{comp_id}">'
                    f'<File Id="{file_id}" Source="{_wix_escape(str(entry))}" KeyPath="yes" />'
                    f"</Component>"
                )
                component_refs.append(f'<ComponentRef Id="{comp_id}" />')
        lines.append(f"{pad}</Directory>")
        return lines

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">',
        "  <Fragment>",
        '    <DirectoryRef Id="INSTALLFOLDER">',
    ]
    for entry in sorted(PORTABLE_DIR.iterdir(), key=lambda p: p.name.lower()):
        if entry.is_dir():
            # PortableFiles 根下的顶层目录（如 _internal）
            sub_id = _sane_id(entry.name, "dir", used_ids)
            lines.extend(emit_dir(entry, sub_id, 3))
        elif entry.is_file():
            comp_id = _sane_id(entry.name, "cmp", used_ids)
            file_id = _sane_id(entry.name, "fil", used_ids)
            lines.append(
                f'      <Component Id="{comp_id}">'
                f'<File Id="{file_id}" Source="{_wix_escape(str(entry))}" KeyPath="yes" />'
                f"</Component>"
            )
            component_refs.append(f'        <ComponentRef Id="{comp_id}" />')
    lines.extend([
        "    </DirectoryRef>",
        '    <ComponentGroup Id="PortableFiles">',
        *component_refs,
        "    </ComponentGroup>",
        "  </Fragment>",
        "</Wix>",
        "",
    ])
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"  -> {len(component_refs)} 个文件写入 {output}")


def build_msi(wix: str) -> None:
    print("编译 WiX MSI 安装包 ...")
    generate_components_wxs(COMPONENTS_WXS)
    subprocess.run(
        [wix, "build", str(WXS_FILE), str(COMPONENTS_WXS),
         "-d", f"AppVersion={APP_VERSION}",
         "-ext", "WixToolset.UI.wixext",
         "-o", str(OUT_MSI)],
        cwd=ROOT, check=True,
    )
    print(f"MSI 安装包: {OUT_MSI.name}")
    # 删除 WiX 调试符号数据库（.wixpdb），仅调试用，不随发布
    pdb = RELEASE_DIR / f"{OUT_MSI.stem}.wixpdb"
    if pdb.exists():
        pdb.unlink()
        print(f"  清理调试符号: {pdb.name}")


def write_sha256_files() -> None:
    """为每个发布产物生成独立的 .sha256 校验文件（sha256sum 格式）。"""
    for path in (OUT_EXE, OUT_MSI, OUT_ZIP):
        if not path.is_file():
            continue
        digest = _sha256(path)
        sidecar = RELEASE_DIR / f"{path.name}.sha256"
        sidecar.write_text(f"{digest}  {path.name}\n", encoding="ascii")
        print(f"  校验文件 : {sidecar.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="一键产出便携版ZIP + EXE + MSI 三件套")
    parser.add_argument("--version", default=APP_VERSION, help="发行版本号，例如 0.0.2 或 1.0.0")
    parser.add_argument("--skip-pyinstaller", action="store_true", help="跳过 PyInstaller（需要已有便携版）")
    parser.add_argument("--skip-zip", action="store_true", help="跳过 ZIP")
    parser.add_argument("--skip-exe", action="store_true", help="跳过 EXE")
    parser.add_argument("--skip-msi", action="store_true", help="跳过 MSI")
    args = parser.parse_args()
    configure_version(args.version)

    if not args.skip_pyinstaller:
        ensure_portable()
    elif not PORTABLE_EXE.is_file() and not any(path.is_file() for path in (OUT_ZIP, OUT_EXE, OUT_MSI)):
        print("便携版不存在且跳过 PyInstaller，无法继续。", file=sys.stderr)
        return 1

    if not args.skip_zip:
        build_zip()
    if not args.skip_exe:
        iscc = find_tool(["ISCC.exe", "iscc"], ISCC_FALLBACKS)
        if not iscc:
            print("未找到 ISCC.exe，请安装 Inno Setup 6: https://jrsoftware.org/isdl.php", file=sys.stderr)
            return 1
        build_exe(iscc)
    if not args.skip_msi:
        wix = find_tool(["wix.exe", "wix"], WIX_FALLBACKS)
        if not wix:
            print("未找到 wix.exe，请安装 WiX Toolset v4: https://github.com/wixtoolset/wix/releases", file=sys.stderr)
            return 1
        build_msi(wix)

    write_sha256_files()
    write_latest_manifest()
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
