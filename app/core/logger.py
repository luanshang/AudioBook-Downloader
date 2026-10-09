# -*- coding: utf-8 -*-
"""
应用日志
========
统一日志配置：
  - 日志目录：<项目根>/logs/（自动创建）
  - 文件：app-YYYY-MM-DD.log（按天轮转）
  - 同时输出到控制台（DEBUG 级）与文件（INFO 级）
  - 异常自动带完整 traceback

用法：
    from app.core.logger import get_logger
    log = get_logger(__name__)
    log.info("...")
    log.error("...", exc_info=True)   # 或直接 log.exception("...")
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

# 项目根目录（app/core/logger.py -> 上溯 3 级）
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LOG_DIR = os.path.join(_ROOT, "logs")

_configured = False


def _ensure_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        pass


def setup_logging(level: int = logging.INFO, log_dir: str = "") -> None:
    """
    初始化全局日志（幂等，重复调用只执行一次）。

    Args:
        level:   根日志级别（默认 INFO）
        log_dir: 自定义日志目录（默认 <项目根>/logs）
    """
    global _configured
    if _configured:
        return
    _configured = True

    if log_dir:
        _LOG_DIR_ACTIVE = log_dir
    else:
        _LOG_DIR_ACTIVE = _LOG_DIR
    _ensure_dir(_LOG_DIR_ACTIVE)

    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 文件输出：按天轮转，保留 7 天
    file_path = os.path.join(_LOG_DIR_ACTIVE, "app.log")
    file_handler = TimedRotatingFileHandler(
        file_path, when="midnight", interval=1,
        backupCount=7, encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # 控制台输出
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    root.addHandler(console)

    logging.info("日志系统初始化完成，日志目录：%s", _LOG_DIR_ACTIVE)


def get_logger(name: str) -> logging.Logger:
    """获取子模块 logger（自动初始化日志系统）。"""
    if not _configured:
        setup_logging()
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, msg: str, exc: Exception) -> None:
    """记录异常（含 traceback），供桥接层统一调用。"""
    logger.error("%s | 异常类型=%s | 详情=%s",
                 msg, type(exc).__name__, exc, exc_info=True)
