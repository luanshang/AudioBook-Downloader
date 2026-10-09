# -*- coding: utf-8 -*-
"""
懒人听书畅听大师 PySide6 版 —— 主窗口
=======================================
功能：搜索(懒人听书/喜马拉雅) / 专辑列表 / 试听播放 / 批量下载 / 格式转换
架构：UI 层仅通过信号/槽与业务层交互，业务逻辑在 app.core 中（无 Qt 依赖）。
表格：QTableView + VirtualTableModel 虚拟模型（按需加载）+ 分页控件
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QObject, Signal, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QComboBox, QListWidget, QListWidgetItem,
    QLabel, QProgressBar, QSlider, QCheckBox, QFileDialog,
    QMessageBox, QSplitter, QTableView, QHeaderView, QSpinBox,
    QAbstractItemView, QMenu, QMenuBar, QInputDialog,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from app.ui.virtual_table import VirtualTableModel

# 每页行数
PAGE_SIZE = 50


class MainWindow(QMainWindow):
    """主窗口。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("懒人听书畅听大师 v2.0")
        self.resize(1024, 720)

        # ---- 业务状态 ----
        self.client = None            # LRTSClient
        self.current_results = []     # 搜索结果 [(type, item)]
        self.current_tracks = []      # 当前专辑曲目（全量元数据）
        self.current_album = {}       # 当前专辑信息
        self.current_album_id = None  # 当前专辑 ID
        self.save_dir = ""            # 保存目录
        self.download_tasks = {}      # index -> DownloadTask
        self.play_index = -1
        self.quality = 2

        # ---- 播放器 ----
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self._build_ui()
        self._build_menu()
        self._connect_signals()

    # ================================================================== #
    # UI 构建
    # ================================================================== #
    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        # --- 顶部：平台 + 搜索 ---
        top = QHBoxLayout()
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["懒人听书", "喜马拉雅"])
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("请输入搜索关键字")
        self.search_box.returnPressed.connect(self.on_search)
        self.search_btn = QPushButton("搜索")
        self.login_btn = QPushButton("用户登录")
        top.addWidget(self.platform_combo)
        top.addWidget(self.search_box, 1)
        top.addWidget(self.search_btn)
        top.addWidget(self.login_btn)
        root.addLayout(top)

        # --- 中部：搜索列表 + 曲目虚拟表格 ---
        splitter = QSplitter(Qt.Horizontal)

        self.result_list = QListWidget()
        self.result_list.setSelectionMode(QAbstractItemView.SingleSelection)

        # 曲目虚拟表格（右侧）
        track_panel = QWidget()
        track_layout = QVBoxLayout(track_panel)
        track_layout.setContentsMargins(0, 0, 0, 0)

        self.track_table = QTableView()
        self.track_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.track_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.track_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.track_table.setAlternatingRowColors(True)
        self.track_table.verticalHeader().setDefaultSectionSize(30)
        # 虚拟模型（按需加载）
        self.track_model = VirtualTableModel(
            headers=["序号", "音频名称", "时长"], total_rows=0)
        self.track_table.setModel(self.track_model)
        # 懒加载数据源（UI 层注入，后台线程调用）
        self.track_model.batch_requester = self._request_track_batch
        self.track_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        track_layout.addWidget(self.track_table)

        # 分页控件（表格下方）
        page_bar = QHBoxLayout()
        self.page_prev_btn = QPushButton("上一页")
        self.page_next_btn = QPushButton("下一页")
        self.page_label = QLabel("第 1/1 页")
        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 1)
        self.page_spin.setPrefix("第 ")
        self.page_spin.setSuffix(" 页")
        self.page_spin.setMaximumWidth(130)
        page_bar.addWidget(self.page_prev_btn)
        page_bar.addWidget(self.page_spin)
        page_bar.addWidget(self.page_label)
        page_bar.addWidget(self.page_next_btn)
        page_bar.addStretch(1)
        track_layout.addLayout(page_bar)

        splitter.addWidget(self.result_list)
        splitter.addWidget(track_panel)
        splitter.setSizes([380, 620])
        root.addWidget(splitter, 1)

        # --- 播放控制条 ---
        play_row = QHBoxLayout()
        self.prev_btn = QPushButton("上一曲")
        self.play_btn = QPushButton("播放")
        self.next_btn = QPushButton("下一曲")
        self.progress_slider = QSlider(Qt.Horizontal)
        self.time_label = QLabel("00:00 / 00:00")
        play_row.addWidget(self.prev_btn)
        play_row.addWidget(self.play_btn)
        play_row.addWidget(self.next_btn)
        play_row.addWidget(self.progress_slider, 1)
        play_row.addWidget(self.time_label)
        root.addLayout(play_row)

        # --- 下载/转换操作条 ---
        op_row = QHBoxLayout()
        self.save_label = QLabel("保存目录: 未选择")
        self.choose_dir_btn = QPushButton("选择目录")
        self.download_one_btn = QPushButton("下载选中")
        self.download_all_btn = QPushButton("下载全部")
        self.download_range_btn = QPushButton("区间下载")
        self.convert_btn = QPushButton("格式转换")
        self.status_label = QLabel("就绪")
        op_row.addWidget(self.choose_dir_btn)
        op_row.addWidget(self.save_label, 1)
        op_row.addWidget(self.download_one_btn)
        op_row.addWidget(self.download_range_btn)
        op_row.addWidget(self.download_all_btn)
        op_row.addWidget(self.convert_btn)
        root.addLayout(op_row)
        root.addWidget(self.status_label)

        # --- 底部状态 ---
        self.detail_progress = QProgressBar()
        self.detail_progress.setTextVisible(False)
        self.detail_progress.hide()
        root.addWidget(self.detail_progress)

        self.setCentralWidget(central)

    def _build_menu(self) -> None:
        bar = QMenuBar(self)
        m_settings = bar.addMenu("设置")
        a_cookie = m_settings.addAction("设置登录会话(Cookie)")
        a_cookie.triggered.connect(self.open_cookie_dialog)
        m_help = bar.addMenu("帮助")
        a_help = m_help.addAction("使用说明")
        a_help.triggered.connect(self.show_help)
        self.setMenuBar(bar)

    # ================================================================== #
    # 信号连接
    # ================================================================== #
    def _connect_signals(self) -> None:
        self.search_btn.clicked.connect(self.on_search)
        self.result_list.itemDoubleClicked.connect(self.on_result_opened)
        self.track_table.doubleClicked.connect(self.on_track_play)
        self.prev_btn.clicked.connect(self.play_prev)
        self.play_btn.clicked.connect(self.play_toggle)
        self.next_btn.clicked.connect(self.play_next)
        self.choose_dir_btn.clicked.connect(self.choose_dir)
        self.download_one_btn.clicked.connect(self.download_selected)
        self.download_all_btn.clicked.connect(self.download_all)
        self.download_range_btn.clicked.connect(self.download_range)
        self.convert_btn.clicked.connect(self.open_converter)
        self.login_btn.clicked.connect(self.open_login)

        # 分页信号
        self.page_prev_btn.clicked.connect(self.page_prev)
        self.page_next_btn.clicked.connect(self.page_next)
        self.page_spin.valueChanged.connect(self.on_page_changed)

        # 播放器信号
        self.player.positionChanged.connect(self.on_pos_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status)

    # ================================================================== #
    # 搜索与列表
    # ================================================================== #
    def on_search(self) -> None:
        keyword = self.search_box.text().strip()
        if not keyword:
            QMessageBox.information(self, "提示", "请输入搜索关键字")
            return
        self.status_label.setText("搜索中...")
        self.result_list.clear()
        self.current_results = []
        self._ensure_client()

        def _do():
            try:
                if self.platform_combo.currentText() == "懒人听书":
                    data = self.client.search(keyword)
                    books = (data.get("data") or {}).get("bookResult", {}).get("list", [])
                    anchors = (data.get("data") or {}).get("announcerResult", {}).get("list", [])
                else:  # 喜马拉雅
                    from app.core.ximalaya_api import search_ximalaya
                    books, anchors = search_ximalaya(self.search_box.text())
                return books, anchors
            except Exception as e:
                return e

        self._run_bg(_do, lambda r: self._on_search_done(r))

    def _on_search_done(self, result) -> None:
        if isinstance(result, Exception):
            self.status_label.setText(f"搜索失败: {result}")
            return
        books, anchors = result
        for b in books:
            self.current_results.append(("book", b))
            item = QListWidgetItem(f"[专辑] {b.get('name', '')}\n{b.get('subTitle', '')}")
            self.result_list.addItem(item)
        for a in anchors:
            self.current_results.append(("anchor", a))
            item = QListWidgetItem(f"[主播] {a.get('name', '')}\n{a.get('description', '')}")
            self.result_list.addItem(item)
        self.status_label.setText(f"搜索完成：{len(self.current_results)} 条")

    # ================================================================== #
    # 选择专辑 -> 加载曲目
    # ================================================================== #
    def on_result_opened(self, item) -> None:
        idx = self.result_list.row(item)
        if idx >= len(self.current_results):
            return
        kind, data = self.current_results[idx]
        self._ensure_client()
        self.status_label.setText("分析中...")
        self.track_model.set_row_count(0)
        self.current_tracks = []

        def _do():
            try:
                if kind == "book":
                    book_id = data.get("id") or data.get("entityId")
                    if not book_id:
                        raise ValueError("缺少专辑ID")
                    detail = self.client.album_detail(book_id)
                    menu = self.client.album_menu(book_id)
                    album_info = detail.get("data") or {}
                    tracks = (menu.get("data") or {}).get("list", [])
                    return {
                        "album": album_info,
                        "tracks": tracks,
                        "book_id": book_id,
                    }
                else:
                    user_id = data.get("userId")
                    albums = self.client.albums_by_user(user_id)
                    return {"albums": (albums.get("data") or {}).get("list", [])}
            except Exception as e:
                return e

        self._run_bg(_do, lambda r: self._on_album_done(kind, r))

    def _on_album_done(self, kind, result) -> None:
        if isinstance(result, Exception):
            self.status_label.setText(f"分析失败: {result}")
            return
        if kind == "book":
            self.current_album = result["album"]
            self.current_album_id = result["book_id"]
            tracks = result["tracks"]
            self._reload_tracks(tracks)
            self.status_label.setText(f"分析完成：{self.current_album.get('name', '')} 共 {len(tracks)} 集")
        else:
            # 主播专辑列表显示到结果列表（标记为可再点开的专辑）
            albums = result.get("albums", [])
            self.result_list.clear()
            self.current_results = []
            for a in albums:
                self.current_results.append(("book", a))
                item = QListWidgetItem(f"[专辑] {a.get('name', '')}\n{a.get('description', '')}")
                self.result_list.addItem(item)
            self.status_label.setText(f"该主播共 {len(albums)} 个专辑，双击打开")

    def _reload_tracks(self, tracks) -> None:
        """填充曲目：设置虚拟模型总行数 + 分页状态。"""
        self.current_tracks = tracks or []
        total = len(self.current_tracks)
        # 虚拟模型：只告诉总行数，数据按需加载
        self.track_model.set_row_count(total)
        self.track_model.set_headers(["序号", "音频名称", "时长"])
        # 分页
        self.total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        self.current_page = 1
        self._update_pager()
        # 清空缓存，从第 0 行开始按需加载
        self._request_track_batch(0, min(PAGE_SIZE, total))

    # ------------------------------------------------------------------ #
    # 分页
    # ------------------------------------------------------------------ #
    def _update_pager(self) -> None:
        """更新分页控件状态。"""
        self.page_spin.setRange(1, max(1, self.total_pages))
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(self.current_page)
        self.page_spin.blockSignals(False)
        self.page_label.setText(f"共 {self.total_pages} 页 / {len(self.current_tracks)} 条")
        self.page_prev_btn.setEnabled(self.current_page > 1)
        self.page_next_btn.setEnabled(self.current_page < self.total_pages)

    def page_prev(self) -> None:
        if self.current_page > 1:
            self.current_page -= 1
            self._update_pager()
            self._show_page(self.current_page)

    def page_next(self) -> None:
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._update_pager()
            self._show_page(self.current_page)

    def on_page_changed(self, value: int) -> None:
        if value != self.current_page:
            self.current_page = value
            self._update_pager()
            self._show_page(value)

    def _show_page(self, page: int) -> None:
        """切换页码：重置模型到对应区间并滚动到顶部。"""
        start = (page - 1) * PAGE_SIZE
        self.track_model.set_row_count(len(self.current_tracks))
        # 清缓存强制重新加载该页
        self.track_model._cache.clear()
        self.track_model._loading.clear()
        self._request_track_batch(start, min(start + PAGE_SIZE, len(self.current_tracks)))
        self.track_table.scrollToTop()

    # ------------------------------------------------------------------ #
    # 虚拟模型懒加载数据源
    # ------------------------------------------------------------------ #
    def _request_track_batch(self, start: int, end: int) -> None:
        """虚拟模型请求数据块：从 current_tracks 取行数据填缓存。"""
        rows = {}
        for r in range(start, end):
            if r >= len(self.current_tracks):
                break
            t = self.current_tracks[r]
            dur = t.get("length", 0) or t.get("duration", 0) or t.get("playCount", 0)
            rows[r] = [str(r + 1), t.get("title", "") or t.get("name", ""),
                       self._fmt_duration(dur)]
        if rows:
            self.track_model.set_row_data(start, rows)

    # ================================================================== #
    # 播放
    # ================================================================== #
    def on_track_play(self, item) -> None:
        row = self.track_table.currentRow()
        self.play_index = row
        self.play_track(row)

    def play_track(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.current_tracks):
            return
        self._ensure_client()

        def _do():
            try:
                t = self.current_tracks[idx]
                return self.client.get_listen_path(t["id"], self.current_album_id, 1, self.quality)
            except Exception as e:
                return e

        def _on(url):
            if isinstance(url, Exception):
                self.status_label.setText(f"获取播放地址失败: {url}")
                return
            self.player.setSource(QUrl(url))
            self.player.play()
            self.play_btn.setText("暂停")
            title = self.current_tracks[idx].get("title", "")
            self.setWindowTitle(f"播放中: {title} - 懒人听书畅听大师")

        self._run_bg(_do, lambda r: _on(r))

    def play_toggle(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("继续播放")
        else:
            self.player.play()
            self.play_btn.setText("暂停")

    def play_prev(self) -> None:
        if hasattr(self, "play_index") and self.play_index > 0:
            self.play_index -= 1
            self.play_track(self.play_index)

    def play_next(self) -> None:
        if hasattr(self, "play_index") and self.play_index + 1 < len(self.current_tracks):
            self.play_index += 1
            self.play_track(self.play_index)

    def on_pos_changed(self, pos: int) -> None:
        duration = self.player.duration()
        if duration > 0:
            self.progress_slider.setMaximum(duration)
            self.progress_slider.setValue(pos)
            self.time_label.setText(f"{self._fmt_ms(pos)} / {self._fmt_ms(duration)}")

    def on_duration_changed(self, dur: int) -> None:
        self.progress_slider.setMaximum(dur)

    def on_media_status(self, status) -> None:
        if status == QMediaPlayer.EndOfMedia:
            self.play_next()

    # ================================================================== #
    # 下载
    # ================================================================== #
    def choose_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "请选择音频下载保存的目录")
        if d:
            self.save_dir = d
            self.save_label.setText(f"保存目录: {d}")

    def download_selected(self) -> None:
        row = self.track_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中要下载的音频")
            return
        if not getattr(self, "save_dir", None):
            QMessageBox.warning(self, "提示", "请先选择保存目录")
            return
        self._download_one(row)

    def download_all(self) -> None:
        if not getattr(self, "save_dir", None):
            QMessageBox.warning(self, "提示", "请先选择保存目录")
            return
        for i in range(len(self.current_tracks)):
            self._download_one(i)

    def download_range(self) -> None:
        # 简化：弹出输入框
        text, ok = QInputDialog.getText(self, "区间下载", "格式: 起始集-结束集 (如 1-10)")
        if not ok or not text:
            return
        try:
            a, b = text.split("-")
            a, b = int(a), int(b)
        except ValueError:
            QMessageBox.warning(self, "提示", "格式错误，应为 1-10")
            return
        for i in range(a - 1, min(b, len(self.current_tracks))):
            self._download_one(i)

    def _download_one(self, idx: int) -> None:
        from app.core.downloader import DownloadTask
        t = self.current_tracks[idx]
        title = t.get("title", f"track_{idx + 1}")
        self._set_track_status(idx, f"{title} (下载中...)")

        dest_dir = Path(self.save_dir) / (self.current_album.get("name", "专辑"))
        dest = str(dest_dir / f"{idx + 1:04d}_{title}.mp3")

        # 获取地址 + 下载在后台线程一并完成
        self._ensure_client()

        def worker():
            try:
                url = self.client.get_listen_path(t["id"], self.current_album_id, 1, self.quality)
                task = DownloadTask(url, dest)
                task.run()
                return task
            except Exception as e:
                return e

        self._run_bg(worker, lambda r: self._on_download_done(idx, r))

    def _set_track_status(self, idx: int, status: str) -> None:
        """更新虚拟模型某行的状态第二列文本。"""
        # 从模型读当前行缓存，只改第一列文本（名称后追加状态）
        row_data = self.track_model._cache.get(idx)
        if row_data and len(row_data) >= 2:
            row_data[1] = status
            self.track_model.set_row_data(idx, {idx: row_data})

    def _on_download_done(self, idx, result) -> None:
        title = self.current_tracks[idx].get("title", "")
        if isinstance(result, Exception):
            self._set_track_status(idx, f"{title} (失败: {result})")
            return
        self._set_track_status(idx, f"{title} (完成)")
        self.status_label.setText(f"下载完成: {title}")

    # ================================================================== #
    # 工作线程工具
    # ================================================================== #
    def _run_bg(self, fn, on_done) -> QThread:
        """在后台线程执行 fn，完成后在主线程调用 on_done 回调。"""
        th = QThread(self)
        worker = _Worker(fn)
        worker.moveToThread(th)
        th.started.connect(worker.run)
        worker.finished.connect(on_done)
        worker.finished.connect(th.quit)
        worker.finished.connect(worker.deleteLater)
        th.finished.connect(th.deleteLater)
        th.start()
        return th

    def _ensure_client(self) -> None:
        if self.client is None:
            from app.core.lrts_api import LRTSClient
            self.client = LRTSClient()

    # ================================================================== #
    # 弹窗入口
    # ================================================================== #
    def open_login(self) -> None:
        from app.ui.login_dialog import LoginDialog
        dlg = LoginDialog(self)
        dlg.exec()

    def open_cookie_dialog(self) -> None:
        from app.ui.cookie_dialog import CookieDialog
        dlg = CookieDialog(self)
        dlg.exec()

    def open_converter(self) -> None:
        from app.ui.converter_dialog import ConverterDialog
        dlg = ConverterDialog(self)
        dlg.exec()

    def show_help(self) -> None:
        QMessageBox.information(self, "使用说明",
            "1. 搜索关键字，选择专辑或主播\n"
            "2. 双击专辑加载曲目列表\n"
            "3. 双击曲目试听，下载前先选择保存目录\n"
            "4. 懒人听书部分接口需登录会话，可在「设置→设置登录会话」粘贴 Cookie")

    # ================================================================== #
    # 工具
    # ================================================================== #
    @staticmethod
    def _fmt_duration(sec) -> str:
        try:
            sec = int(sec)
        except (TypeError, ValueError):
            return "--:--"
        return f"{sec // 60:02d}:{sec % 60:02d}"

    @staticmethod
    def _fmt_ms(ms: int) -> str:
        sec = ms // 1000
        return f"{sec // 60:02d}:{sec % 60:02d}"


class _Worker(QObject):
    """通用后台任务（fn 返回结果，通过信号回主线程）。"""

    finished = Signal(object)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self) -> None:
        try:
            self.finished.emit(self.fn())
        except Exception as e:
            self.finished.emit(e)