# -*- coding: utf-8 -*-
"""
有声书下载器 v2.0 —— FluentUI QML 版入口
=============================================
启动：python main.py
架构：QML(FluentUI 无边框窗口 + 侧边栏) + Python 桥接层(app.bridge)
日志：logs/app.log（按天轮转，保留 7 天），异常自动记录完整 traceback
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    # 高 DPI + 确保可找到 FluentUI 包
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

    # 初始化日志系统（必须在其他模块导入前，让所有 logger 可用）
    from app.core.logger import setup_logging, get_logger
    setup_logging()
    log = get_logger("main")
    log.info("========== 有声书下载器启动 ==========")

    # 导入 QML 资源模块（必须先导入以注册资源）
    from app.qml import app_qml_rc  # noqa: F401
    from FluentUI.imports import resource_rc  # noqa: F401

    from PySide6.QtCore import QUrl, QObject, Signal, Slot, Property
    from PySide6.QtWidgets import QApplication
    from PySide6.QtQml import QQmlApplicationEngine

    from FluentUI import FluentUI
    from app.bridge.bridge import Bridge
    from app.core.settings import AppSettings


    class SettingsBridge(QObject):
        """QML 可访问的设置对象。"""

        saveDirChanged = Signal(str)

        def __init__(self, parent=None):
            super().__init__(parent)
            self._save_dir = AppSettings.save_dir()

        @Slot(str)
        def set_save_dir(self, path: str) -> None:
            self._save_dir = path
            AppSettings.set_save_dir(path)
            self.saveDirChanged.emit(path)

        @Slot(result=str)
        def get_save_dir(self) -> str:
            return self._save_dir

        saveDir = Property(str, get_save_dir, set_save_dir, notify=saveDirChanged)

        @Slot(bool)
        def saveUseSystemAppBar(self, enabled: bool) -> None:
            AppSettings.set("UseSystemAppBar", bool(enabled))

        @Slot(bool)
        def save_use_system_app_bar(self, enabled: bool) -> None:
            self.saveUseSystemAppBar(enabled)

        @Slot(result=bool)
        def loadUseSystemAppBar(self) -> bool:
            return bool(AppSettings.get("UseSystemAppBar", False))

        @Slot(result=bool)
        def load_use_system_app_bar(self) -> bool:
            return self.loadUseSystemAppBar()

        @Slot(result=bool)
        def load_disclaimer_ack(self) -> bool:
            return bool(AppSettings.get("CopyrightDisclaimerAcknowledged", False))

        @Slot()
        def acknowledge_disclaimer(self) -> None:
            AppSettings.set("CopyrightDisclaimerAcknowledged", True)

        @Slot(int)
        def save_dark_mode(self, mode: int) -> None:
            AppSettings.set("DarkMode", mode)

        @Slot(int)
        def saveDarkMode(self, mode: int) -> None:
            self.save_dark_mode(mode)

        @Slot(result=int)
        def loadDarkMode(self) -> int:
            return self.load_dark_mode()


    app = QApplication(sys.argv)
    app.setOrganizationName("AudioMaster")
    app.setApplicationName("有声书下载器")
    app.setApplicationDisplayName("有声书下载器")

    engine = QQmlApplicationEngine()
    FluentUI.registerTypes(engine)

    # 主题初始化：优先读取上次选择，否则跟随系统（QML 加载前设置）
    from FluentUI.FluTheme import FluTheme
    from FluentUI.Def import FluThemeType
    saved_mode = AppSettings.get("DarkMode", None)
    if saved_mode is not None:
        try:
            FluTheme().darkMode = int(saved_mode)
        except Exception:
            FluTheme().darkMode = FluThemeType.DarkMode.System
    else:
        FluTheme().darkMode = FluThemeType.DarkMode.System
    FluTheme().animationEnabled = True

    # 注册桥接对象与设置
    bridge = Bridge()
    bridge.set_webengine_application(app)
    settings = SettingsBridge()
    engine.rootContext().setContextProperty("Bridge", bridge)
    engine.rootContext().setContextProperty("Settings", settings)
    engine.rootContext().setContextProperty("AppBridge", settings)

    qml_file = QUrl("qrc:/qml/App.qml")
    engine.load(qml_file)
    if not engine.rootObjects():
        log.error("QML 加载失败：%s", qml_file)
        sys.exit(-1)
    log.info("QML 界面加载成功")

    # 全局未捕获异常钩子：记录到日志后仍交给默认处理
    def _excepthook(exc_type, exc_value, exc_tb):
        log.error("未捕获异常", exc_info=(exc_type, exc_value, exc_tb))
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
