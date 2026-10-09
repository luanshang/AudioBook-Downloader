# -*- coding: utf-8 -*-
"""
用户登录对话框
==============
微信小程序扫码登录懒人听书：
  1. 打开微信登录页（懒人听书小程序）
  2. 提示用户扫码后粘贴 Cookie / 或直接扫码后自动检测
保留手动粘贴会话方式（与原版 setCookie 窗体一致）。
"""

from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QPlainTextEdit, QMessageBox,
)


class LoginDialog(QDialog):
    """用户登录对话框（扫码 + 粘贴会话）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("用户登录")
        self.resize(480, 360)

        self.parent_win = parent
        self._cookie = ""

        vbox = QVBoxLayout(self)

        vbox.addWidget(QLabel("方式一：扫码登录（懒人听书微信小程序）"))

        row = QHBoxLayout()
        open_btn = QPushButton("打开微信登录页")
        open_btn.clicked.connect(self._open_wechat_login)
        row.addWidget(open_btn)
        row.addStretch(1)
        vbox.addLayout(row)

        vbox.addSpacing(12)
        vbox.addWidget(QLabel("方式二：粘贴登录会话 Cookie（可联系作者协助抓包）"))

        self.cookie_edit = QPlainTextEdit()
        self.cookie_edit.setPlaceholderText("将手机抓包获取的 Cookie 粘贴到这里...")
        self.cookie_edit.setMaximumHeight(120)
        vbox.addWidget(self.cookie_edit)

        test_btn = QPushButton("测试会话")
        test_btn.clicked.connect(self._test_cookie)
        vbox.addWidget(test_btn)

        self.status_label = QLabel("信息")
        vbox.addWidget(self.status_label)

        btns = QHBoxLayout()
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("关闭")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch(1)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        vbox.addLayout(btns)

    def _open_wechat_login(self) -> None:
        webbrowser.open("https://m.lrts.me/login?redirectUrl=%2Fuser")

    def _test_cookie(self) -> None:
        cookie = self.cookie_edit.toPlainText().strip()
        if not cookie:
            self.status_label.setText("请输入最新的会话 Cookie")
            return
        try:
            from app.core.lrts_api import LRTSClient
            client = LRTSClient(cookie)
            info = client.get_user_info()
            data = info.get("data") or {}
            if data.get("userId"):
                self._cookie = cookie
                nickname = data.get("nickname", "")
                self.status_label.setText(f"测试成功：{nickname}（会员有效期见个人中心）")
            else:
                self.status_label.setText("测试失败，请获取最新的会话")
        except Exception as e:
            self.status_label.setText(f"测试失败：{e}")

    def _save(self) -> None:
        cookie = self._cookie or self.cookie_edit.toPlainText().strip()
        if not cookie:
            QMessageBox.warning(self, "提示", "请先粘贴并测试会话 Cookie")
            return
        # 保存到配置
        from app.core.settings import AppSettings
        AppSettings.set("UserCookie", cookie)
        AppSettings.set("UserLogin", True)
        if self.parent_win and hasattr(self.parent_win, "client"):
            self.parent_win.client.set_cookie(cookie)
        QMessageBox.information(self, "成功", "登录会话已保存")
        self.accept()