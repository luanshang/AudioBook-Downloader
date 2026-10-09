# -*- mode: python ; coding: utf-8 -*-
# 有声书下载器 安装器打包脚本（PySide6 + FluentUI 无边框向导）
# 用法: pyinstaller setup.spec --noconfirm --clean
# 产物: dist/有声书下载器_安装版_v0.0.1.exe (单文件安装器)

import os
from pathlib import Path

ROOT = Path(SPECPATH)
PROJECT = ROOT.parent.parent
PKG = Path(os.environ.get('AUDIOBOOK_PACKAGE_STAGING', ROOT / 'pkg_tmp'))

# 将便携版全部内容作为 app/ 数据打包（保留顶层目录名，如 app/_internal/...）
datas = []
for name in sorted(os.listdir(PKG)):
    s = os.path.join(PKG, name)
    # 目标路径: app/<name>，目录和文件都保留原始名称与结构
    datas.append((s, os.path.join('app', name)))

# FluentUI QML 资源与字体（resource_rc.py 已编译进 qrc，字体图标等仍在目录中）
fluentui_dir = PROJECT / 'FluentUI'
datas.append((str(fluentui_dir), 'FluentUI'))

# 安装向导 QML 界面
qml_dir = ROOT / 'setup_qml'
if qml_dir.exists():
    datas.append((str(qml_dir), 'setup_qml'))

# PyInstaller 需收集 FluentUI Python 模块（纯 Python + 编译后的 resource_rc）
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('FluentUI')
hiddenimports += [
    'FluentUI.imports.resource_rc',
    'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets',
    'PySide6.QtWidgets', 'PySide6.QtGui', 'PySide6.QtCore',
    'shiboken6',
]

a = Analysis(
    ['setup_gui.py'],
    pathex=[str(ROOT), str(PROJECT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='有声书下载器_安装版_v0.0.1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # 安装器：GUI 消息框，无控制台
    disable_windowed_traceback=False,
    icon=str(ROOT / 'installer_icon.ico'),
)