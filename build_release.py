#!/usr/bin/env python3
"""Build the portable package, optionally followed by the one-file installer."""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QRC = ROOT / "app" / "qml" / "resource.qrc"
QRC_PY = ROOT / "app" / "qml" / "app_qml_rc.py"
INSTALLER_SPEC = ROOT / "_tools" / "setup.spec"
INSTALLER_NAME = "有声书下载器_安装版_v2.0.0.exe"
RELEASE_DIR = ROOT / "Release"
RELEASE_PORTABLE_DIR = RELEASE_DIR / "有声书下载器_便携版"
RELEASE_INSTALLER = RELEASE_DIR / INSTALLER_NAME


def run(args: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    command = [str(sys.executable), *args]
    print("\n> " + " ".join(f'"{item}"' if " " in item else item for item in command))
    subprocess.run(command, cwd=cwd, env=env, check=True)


def find_rcc() -> Path:
    spec = importlib.util.find_spec("PySide6")
    if spec and spec.origin:
        candidate = Path(spec.origin).parent / "rcc.exe"
        if candidate.is_file():
            return candidate
    candidate = shutil.which("pyside6-rcc") or shutil.which("rcc")
    if candidate:
        return Path(candidate)
    raise FileNotFoundError(
        "找不到 PySide6 rcc.exe。请确认当前 Python 环境已安装 PySide6。"
    )


def compile_qml_resources() -> None:
    rcc = find_rcc()
    print(f"\n[1/3] 编译 QML 资源: {rcc}")
    subprocess.run(
        [str(rcc), "--generator", "python", str(QRC), "-o", str(QRC_PY)],
        cwd=ROOT,
        check=True,
    )


def build_portable(work_dir: Path) -> Path:
    print("\n[2/3] 打包便携版")
    dist_dir = work_dir / "dist"
    build_dir = work_dir / "build"
    run([
        "-m", "PyInstaller", str(ROOT / "lrts.spec"),
        "--noconfirm", "--clean",
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
    ])
    portable_dir = dist_dir / "有声书下载器_便携版"
    exe = portable_dir / "有声书下载器.exe"
    if not exe.is_file():
        raise FileNotFoundError(f"便携版主程序不存在: {exe}")
    return portable_dir


def verify_qml_startup() -> None:
    print("\n[3/3] 验证 QML 页面启动")
    script = '''
import sys
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
import app.qml.app_qml_rc
from FluentUI import FluentUI
app = QGuiApplication(sys.argv)
engine = QQmlApplicationEngine()
FluentUI.registerTypes(engine)
engine.load(QUrl("qrc:/qml/App.qml"))
if not engine.rootObjects():
    raise SystemExit("QML root object failed to load")
def check_main_window():
    if not any(window.isVisible() for window in app.topLevelWindows()):
        print("QML main window failed to become visible", file=sys.stderr)
        app.exit(1)
        return
    app.quit()
QTimer.singleShot(1000, check_main_window)
sys.exit(app.exec())
'''
    import os
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    subprocess.run([str(sys.executable), "-c", script], cwd=ROOT, env=env, check=True)


def stage_portable(portable_dir: Path, staging_dir: Path) -> None:
    print(f"\n[4/6] 准备安装器输入目录: {staging_dir}")
    shutil.copytree(portable_dir, staging_dir)


def build_installer(work_dir: Path, staging_dir: Path) -> Path:
    print("\n[5/6] 打包安装器")
    env = os.environ.copy()
    env["AUDIOBOOK_PACKAGE_STAGING"] = str(staging_dir)
    dist_dir = work_dir / "installer_dist"
    build_dir = work_dir / "installer_build"
    run([
        "-m", "PyInstaller", str(INSTALLER_SPEC),
        "--noconfirm", "--clean",
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
    ], env=env)
    installer = dist_dir / "有声书下载器_安装版_v2.0.0.exe"
    if not installer.is_file():
        raise FileNotFoundError(f"安装器不存在: {installer}")
    return installer


def publish(portable_dir: Path, installer: Path | None) -> None:
    print(f"\n[发布] 汇总文件到: {RELEASE_DIR}")
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(portable_dir, RELEASE_PORTABLE_DIR, dirs_exist_ok=True)
    if installer is not None:
        shutil.copy2(installer, RELEASE_INSTALLER)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="默认生成便携版；传入 -i/--installer 时同时生成安装包。"
    )
    parser.add_argument(
        "-i",
        "--installer",
        action="store_true",
        help="同时打包单文件安装包。默认只打包便携版。",
    )
    parser.add_argument(
        "--skip-qml",
        action="store_true",
        help="跳过 QML 资源编译，使用现有 app_qml_rc.py。",
    )
    args = parser.parse_args()

    try:
        if not args.skip_qml:
            compile_qml_resources()
        else:
            print("\n[1/3] 跳过 QML 资源编译")
        with tempfile.TemporaryDirectory(prefix="audiobook-build-") as temp_dir:
            work_dir = Path(temp_dir)
            portable_dir = build_portable(work_dir)
            verify_qml_startup()
            installer = None
            if args.installer:
                staging_dir = work_dir / "pkg_tmp"
                stage_portable(portable_dir, staging_dir)
                installer = build_installer(work_dir, staging_dir)
            publish(portable_dir, installer)
    except subprocess.CalledProcessError as exc:
        print(f"\n打包失败，退出码: {exc.returncode}", file=sys.stderr)
        return exc.returncode or 1
    except (FileNotFoundError, OSError) as exc:
        print(f"\n打包失败: {exc}", file=sys.stderr)
        return 1

    print("\n打包完成:")
    print(f"  便携版: {RELEASE_PORTABLE_DIR}")
    if args.installer:
        print(f"  安装器: {RELEASE_INSTALLER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
