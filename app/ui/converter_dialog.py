# -*- coding: utf-8 -*-
"""
格式转换对话框
===============
M4A -> MP3 批量转换（ffmpeg）。
支持：音质选择 / 倍速选择 / 拖拽目录 / 转换日志。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QPlainTextEdit, QFileDialog, QMessageBox,
)


class ConverterDialog(QDialog):
    """音频格式转换工具。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("音频格式转换工具")
        self.resize(620, 520)

        self.src_dir = ""
        self._worker = None

        vbox = QVBoxLayout(self)

        row = QHBoxLayout()
        self.dir_edit = QLineEdit()
        self.dir_edit.setPlaceholderText("可拖拽文件夹到本界面")
        self.dir_edit.setAcceptDrops(True)
        self.dir_edit.dragEnterEvent = self._drag_enter
        self.dir_edit.dropEvent = self._drop
        btn = QPushButton("选择目录")
        btn.clicked.connect(self._choose_dir)
        row.addWidget(btn)
        row.addWidget(self.dir_edit, 1)
        vbox.addLayout(row)

        cfg = QHBoxLayout()
        cfg.addWidget(QLabel("文件转换类型"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["M4A->MP3"])
        cfg.addWidget(self.type_combo)
        cfg.addSpacing(16)
        cfg.addWidget(QLabel("输出音频质量"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["低音质", "中音质", "高音质", "超高音质"])
        self.quality_combo.setCurrentText("高音质")
        cfg.addWidget(self.quality_combo)
        cfg.addSpacing(16)
        cfg.addWidget(QLabel("音频播放倍数"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5倍", "0.8倍", "1.0倍", "1.25倍", "1.5倍", "2.0倍"])
        cfg.addWidget(self.speed_combo)
        cfg.addStretch(1)
        vbox.addLayout(cfg)

        go_btn = QPushButton("执行转换")
        go_btn.clicked.connect(self._convert)
        vbox.addWidget(go_btn)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        vbox.addWidget(self.log, 1)

    # ---- 拖拽 ----
    def _drag_enter(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drop(self, event):
        urls = event.mimeData().urls()
        if urls:
            p = Path(urls[0].toLocalFile())
            if p.is_dir():
                self.src_dir = str(p)
                self.dir_edit.setText(str(p))

    def _choose_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "请选择需要转换音频的目录")
        if d:
            self.src_dir = d
            self.dir_edit.setText(d)

    # ---- 转换 ----
    def _convert(self) -> None:
        from app.core.converter import Converter

        if not Path(self.src_dir).is_dir():
            self.log.setPlainText("请指定正确的目录")
            return

        self.log.clear()
        converter = Converter(
            quality=self.quality_combo.currentText(),
            speed=self.speed_combo.currentText(),
        )

        # 后台线程转换，避免卡界面
        from PySide6.QtCore import QThread, QObject, Signal

        class _Worker(QObject):
            done = Signal(object)

            def __init__(self, fn):
                super().__init__()
                self.fn = fn

            def run(self):
                try:
                    self.done.emit(self.fn())
                except Exception as e:
                    self.done.emit(e)

        th = QThread(self)
        self._worker = _Worker(lambda: converter.convert_folder(
            self.src_dir, progress_cb=self.log.appendPlainText))
        self._worker.moveToThread(th)
        th.started.connect(self._worker.run)
        self._worker.done.connect(lambda r: self._on_done(r))
        self._worker.done.connect(th.quit)
        self._worker.done.connect(self._worker.deleteLater)
        th.finished.connect(th.deleteLater)
        th.start()

    def _on_done(self, result) -> None:
        if isinstance(result, Exception):
            self.log.appendPlainText(f"转换失败：{result}")
            return
        ok, skipped = result
        self.log.appendPlainText(f"恭喜你，格式转换全部完成！共 {ok} 个文件，跳过 {skipped} 个。")