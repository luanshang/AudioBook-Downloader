# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec —— 有声书下载器 v2.0 (FluentUI QML 版) 便携版
# 使用：pyinstaller lrts.spec

import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent.parent

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # 内置资源（图标、ffmpeg 如有）
        (str(ROOT / 'app' / 'resources'), 'app/resources'),
        # FluentUI 的 QML 资源（imports 里的 qmldir/qml 需要随包）
        (str(ROOT / 'FluentUI' / 'imports'), 'FluentUI/imports'),
    ],
    hiddenimports=[
        'PySide6.QtMultimedia',
        'PySide6.QtQml',
        'PySide6.QtWidgets',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtQuick',
        'keyboard',
        'app.core.lrts_api',
        'app.core.ximalaya_api',
        'app.core.qidian_api',
        'app.core.decrypt',
        'app.core.downloader',
        'app.core.converter',
        'app.core.settings',
        'app.bridge.bridge',
        'app.qml.app_qml_rc',
        'FluentUI.imports.resource_rc',
        'FluentUI.FluentUI',
        'FluentUI.FluApp',
        'FluentUI.FluTheme',
        'FluentUI.FluFrameless',
        'FluentUI.FluTools',
        'FluentUI.FluentIconDef',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='有声书下载器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # GUI 程序，不弹控制台
    disable_windowed_traceback=False,
    icon=str(ROOT / 'app' / 'resources' / 'favicon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='有声书下载器_便携版',
)