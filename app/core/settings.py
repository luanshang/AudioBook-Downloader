# -*- coding: utf-8 -*-
"""
应用设置
=========
基于 QSettings 持久化（对应原版 config.table）：
  - 登录会话 Cookie
  - 保存目录
  - 会员状态
"""

from __future__ import annotations

from PySide6.QtCore import QSettings

_APP_NAME = "lrts-master"
_ORG = "AudioMaster"


class AppSettings:
    """QSettings 封装。"""

    _settings = QSettings(_ORG, _APP_NAME)

    @classmethod
    def get(cls, key: str, default=None):
        return cls._settings.value(key, default)

    @classmethod
    def set(cls, key: str, value) -> None:
        cls._settings.setValue(key, value)

    @classmethod
    def cookie(cls) -> str:
        return cls.get("UserCookie", "") or ""

    @classmethod
    def save_dir(cls) -> str:
        return cls.get("SaveDir", "") or ""

    @classmethod
    def set_save_dir(cls, path: str) -> None:
        cls.set("SaveDir", path)