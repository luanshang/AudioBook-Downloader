# -*- coding: utf-8 -*-
"""
有声书下载器 安装向导（PySide6 + FluentUI 无边框版）
=====================================================
用法：
  python _tools/setup_gui.py                # 图形安装向导
  LRTS_SETUP_SILENT=1 python _tools/setup_gui.py   # 静默安装

界面：FluWindow 无边框窗口 + FluAppBar，欢迎/路径/进度/完成 四页。
安装逻辑复用 setup_main.py 的 do_install / create_shortcut。
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

# 允许从 _tools 目录直接运行（setup_main 与 setup_qml 同目录）
_TOOLS_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _TOOLS_DIR.parent
for _p in (_TOOLS_DIR, _PROJECT_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from setup_main import APP_NAME, APP_VERSION, EXE_NAME, all_users_install_dir, do_install, run_silent  # noqa: E402


def _is_admin() -> bool:
    if os.name != "nt":
        return True
    import ctypes
    return bool(ctypes.windll.shell32.IsUserAnAdmin())


def _relaunch_as_admin(target: str, make_shortcut: bool) -> bool:
    import ctypes
    params = subprocess.list2cmdline(["--elevated-install", target, "1" if make_shortcut else "0"])
    result = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, str(Path(sys.executable).parent), 1
    )
    return result > 32

from PySide6.QtCore import QObject, QUrl, Signal, Slot, Property
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtQml import QQmlApplicationEngine

from FluentUI import FluentUI


def _run_elevated_install(target: str, make_shortcut: bool) -> int:
    error = do_install(target, make_shortcut)
    if error:
        print(f"安装失败：{error}", file=sys.stderr)
        return 1
    return 0


class InstallerBridge(QObject):
    """QML 可访问的安装桥接对象。"""

    progressChanged = Signal(float, str)
    installFinished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._install_dir = ""
        from setup_main import default_install_dir
        self._install_dir = default_install_dir()
        self._app_exe = ""

    @Property(str, constant=True)
    def appName(self):
        return APP_NAME

    @Property(str, constant=True)
    def appVersion(self):
        return APP_VERSION

    @Property(str, notify=installFinished)
    def installDir(self):
        return self._install_dir

    @Property(str, constant=True)
    def allUsersInstallDir(self):
        return all_users_install_dir()
    @Slot(result=str)
    def browseDirectory(self, initial: str = "") -> str:
        """打开目录选择对话框，返回所选目录（取消则返回空串）。"""
        start = initial or self._install_dir
        selected = QFileDialog.getExistingDirectory(None, "选择安装目录", start)
        return selected

    @Slot(str, bool, bool)
    def startInstall(self, target: str, make_shortcut: bool, all_users: bool) -> None:
        """后台线程执行安装，进度通过 progressChanged 上报。"""
        if all_users and not _is_admin():
            _relaunch_as_admin(target, make_shortcut)
            return
        self._install_dir = target

        def worker():
            def progress(value, text):
                self.progressChanged.emit(float(value), str(text))

            error = do_install(target, make_shortcut, progress)
            if error is None:
                self._install_dir = target
                self._app_exe = os.path.join(target, EXE_NAME)
            else:
                self.progressChanged.emit(0.0, f"安装失败：{error}")
            self.installFinished.emit()

        threading.Thread(target=worker, daemon=True).start()

    @Slot()
    def launchApp(self) -> None:
        """启动已安装的主程序。"""
        if self._app_exe and os.path.isfile(self._app_exe):
            subprocess.Popen([self._app_exe], cwd=os.path.dirname(self._app_exe))

    @Slot(str)
    def showMessage(self, text: str) -> None:
        """简单的提示（QML 无原生 MessageBox 时用）。"""
        from PySide6.QtWidgets import QMessageBox
        box = QMessageBox()
        box.setWindowTitle(f"{APP_NAME} 安装")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setText(text)
        box.exec()


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "--elevated-install":
        target = sys.argv[2]
        make_shortcut = len(sys.argv) < 4 or sys.argv[3] == "1"
        return _run_elevated_install(target, make_shortcut)
    if os.environ.get("LRTS_SETUP_SILENT") == "1":
        return run_silent()

    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

    app = QApplication(sys.argv)
    app.setOrganizationName("AudioMaster")
    app.setApplicationName(f"{APP_NAME} 安装向导")

    engine = QQmlApplicationEngine()
    FluentUI.registerTypes(engine)

    # 主题默认跟随系统（安装向导不做主题持久化）
    from FluentUI.FluTheme import FluTheme
    from FluentUI.Def import FluThemeType
    FluTheme().darkMode = FluThemeType.DarkMode.System
    FluTheme().animationEnabled = True

    bridge = InstallerBridge()
    engine.rootContext().setContextProperty("Installer", bridge)

    qml_file = _TOOLS_DIR / "setup_qml" / "SetupApp.qml"
    if not qml_file.exists():
        # 打包后（PyInstaller _MEIPASS 内）
        bundled = Path(getattr(sys, "_MEIPASS", _TOOLS_DIR)) / "setup_qml" / "SetupApp.qml"
        qml_file = bundled
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        print("QML 加载失败：", qml_file, file=sys.stderr)
        return -1

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
