# -*- coding: utf-8 -*-
"""
虚拟表格模型（按需加载）
========================
基于 QAbstractTableModel 实现，适用于超大数据集：
  - 仅实例化用户可见区域的 item，滚动时才请求数据
  - 配合 QTableView 的 setModel，天然虚拟化（Qt 只渲染可见区域）

本模型支持：
  - 懒加载：fetchMore / canFetchMore（按页拉取）
  - 外形数据加载：rowCount 固定为总行数，data() 按需返回
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex


class VirtualTableModel(QAbstractTableModel):
    """按需加载的虚拟表格模型。

    Args:
        headers: 表头列表
        total_rows: 总行数（可先给估算值，之后 set_row_count 更新）
        fetch_batch: 后台线程每次拉取的行数
    """

    def __init__(self, headers: list[str], total_rows: int = 0,
                 fetch_batch: int = 500):
        super().__init__()
        self._headers = headers
        self._row_count = total_rows
        self._cache: dict[int, list[Any]] = {}  # row -> cell values
        self._loading: set[int] = set()         # 正在加载的行
        self._fetch_batch = fetch_batch
        # 数据源回调（外部注入，在后台线程调用）
        self.data_loader: Optional[Callable[[int, int], dict[int, list[Any]]]] = None
        # 批量请求回调（UI 层设置，用于把数据源线程和模型绑定）
        self.batch_requester: Optional[Callable[[int, int], None]] = None
        # 外设：选中行变化回调
        self.selection_changed: Optional[Callable[[int], None]] = None

    # ------------------------------------------------------------------ #
    # Qt 虚函数
    # ------------------------------------------------------------------ #
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else self._row_count

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._headers)

    def headerData(self, section: int, orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._headers[section] if section < len(self._headers) else ""
        return str(section + 1)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        # 触发懒加载：行数据不在缓存且未在加载中
        if row not in self._cache and row not in self._loading and self.batch_requester:
            self._loading.add(row)
            self.batch_requester(row, row + 1)
        if role == Qt.DisplayRole:
            row_data = self._cache.get(row)
            if row_data and col < len(row_data):
                return row_data[col]
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif role == Qt.TextColorRole:
            # 状态列颜色（下载中/完成/失败）
            row_data = self._cache.get(row)
            if row_data and len(row_data) > 0:
                st = row_data[-1]
                if isinstance(st, str) and "完成" in st:
                    return Qt.green
                if isinstance(st, str) and ("失败" in st or "无权限" in st):
                    return Qt.red
                if isinstance(st, str) and "下载中" in st:
                    return Qt.blue
        return None

    # ------------------------------------------------------------------ #
    # 懒加载（批量请求）
    # ------------------------------------------------------------------ #
    def _request_batch(self, start: int, end: int) -> None:
        """请求一个数据块：由 data() 命中未缓存行时触发。"""
        if self.batch_requester is None:
            return
        for row in range(start, end):
            if row < self._row_count:
                self._loading.add(row)
        self.batch_requester(start, end)

    def set_row_data(self, start: int, data: dict[int, list[Any]]) -> None:
        """后台线程加载完成后调用，填充缓存并通知表格刷新。"""
        self._cache.update(data)
        for row in data:
            self._loading.discard(row)
        if data:
            top = min(data)
            bottom = max(data)
            self.dataChanged.emit(
                self.index(top, 0), self.index(bottom, len(self._headers) - 1)
            )

    # ------------------------------------------------------------------ #
    # 控制
    # ------------------------------------------------------------------ #
    def set_row_count(self, count: int) -> None:
        """数据总量变化时更新（如翻页后）。"""
        self.beginResetModel()
        self._row_count = count
        self._cache.clear()
        self._loading.clear()
        self.endResetModel()

    def set_headers(self, headers: list[str]) -> None:
        self.beginResetModel()
        self._headers = headers
        self.endResetModel()

    def clear(self) -> None:
        self.set_row_count(0)

    def total_rows(self) -> int:
        return self._row_count

    # 供 UI 层批量加载完成后的回调
    def on_batch_loaded(self, rows: dict[int, list[Any]]) -> None:
        self.set_row_data(min(rows) if rows else 0, rows)