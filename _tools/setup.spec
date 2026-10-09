# -*- mode: python ; coding: utf-8 -*-
# 有声书下载器 安装器打包脚本
# 用法: pyinstaller setup.spec --noconfirm --clean
# 产物: dist/有声书下载器_安装版_v2.0.0.exe (单文件安装器)

import os
from pathlib import Path

ROOT = Path(SPECPATH)
PKG = Path(os.environ.get('AUDIOBOOK_PACKAGE_STAGING', ROOT / 'pkg_tmp'))

# 将便携版全部内容作为 app/ 数据打包（保留顶层目录名，如 app/_internal/...）
datas = []
for name in sorted(os.listdir(PKG)):
    s = os.path.join(PKG, name)
    # 目标路径: app/<name>，目录和文件都保留原始名称与结构
    datas.append((s, os.path.join('app', name)))

a = Analysis(
    ['setup_main.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6', 'shiboken6', 'tkinter'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='有声书下载器_安装版_v2.0.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # 安装器：GUI 消息框，无控制台
    disable_windowed_traceback=False,
    icon=str(ROOT.parent / 'app' / 'resources' / 'favicon.ico'),
)