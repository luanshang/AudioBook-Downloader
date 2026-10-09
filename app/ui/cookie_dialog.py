# -*- coding: utf-8 -*-
"""
设置登录会话对话框（Cookie）
=============================
与原版 setCookie 窗体一致：粘贴 Cookie -> 测试 -> 保存。
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QMessageBox,
)


class CookieDialog(QDialog):
    """手动设置登录会话。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置用户登录会话")
        self.resize(520, 360)

        self.parent_win = parent

        vbox = QVBoxLayout(self)
        vbox.addWidget(QLabel("请获取最新的会话 Cookie（可联系作者协助抓包会话）"))

        self.cookie_edit = QPlainTextEdit()
        self.cookie_edit.setPlaceholderText("粘贴 Cookie...")
        vbox.addWidget(self.cookie_edit)

        self.status_label = QLabel("信息")
        vbox.addWidget(self.status_label)

        row = QHBoxLayout()
        test_btn = QPushButton("测试会话")
        test_btn.clicked.connect(self._test)
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self._save)
        row.addStretch(1)
        row.addWidget(test_btn)
        row.addWidget(save_btn)
        vbox.addLayout(row)

    def _test(self) -> None:
        cookie = self.cookie_edit.toPlainText().strip()
        if not cookie:
            self.status_label.setText("请输入最新的会话")
            return
        try:
            from app.core.lrts_api import LRTSClient
            info = LRTSClient(cookie).get_user_info()
            data = info.get("data") or {}
            if data.get("userId"):
                self._valid_cookie = cookie
                self.status_label.setText(f"测试成功：{data.get('nickname', '')}")
            else:
                self.status_label.setText("测试失败，请获取最新的会话")
        except Exception as e:
            self.status_label.setText(f"测试失败：{e}")

    def _save(self) -> None:
        cookie = getattr(self, "_valid_cookie", "") or self.cookie_edit.toPlainText().strip()
        if not cookie:
            QMessageBox.warning(self, "提示", "请先测试会话")
            return
        from app.core.settings import AppSettings
        AppSettings.set("UserCookie", cookie)
        AppSettings.set("UserLogin", True)
        if self.parent_win and hasattr(self.parent_win, "client"):
            self.parent_win.client.set_cookie(cookie)
        QMessageBox.information(self, "成功", "会话已保存")
        self.accept()