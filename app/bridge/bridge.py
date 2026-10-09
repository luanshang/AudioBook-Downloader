# -*- coding: utf-8 -*-
"""
QML 后端桥接层
==============
将 app.core 的业务能力暴露给 QML 界面。
使用 QObject + Signal/Slot 与 QML 通信，后台任务用 QThreadPool。
所有后台任务异常统一记录到 logs/（见 app.core.logger）。
"""

from __future__ import annotations

import threading
import json
from typing import Any, Optional

from PySide6.QtCore import QObject, Signal, Slot, QThreadPool, QRunnable, QUrl, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEnginePage,
    QWebEngineUrlRequestInterceptor,
)

from app.core.logger import get_logger

log = get_logger(__name__)


class _LoginPage(QWebEnginePage):
    """保留登录/播放器页面，拦截 App Scheme 和应用商店跳转。"""

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if url.scheme() == "lazyaudio":
            return False
        if url.host() in ("apps.apple.com", "play.google.com"):
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)


class _LoginRequestInterceptor(QWebEngineUrlRequestInterceptor):
    """从内置浏览器实际发出的同域请求中捕获 HttpOnly Cookie。"""

    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def interceptRequest(self, info) -> None:
        url = info.requestUrl()
        if not url.host().endswith("lrts.me"):
            return
        try:
            # QWebEngineUrlRequestInfo 使用 httpHeaders()；requestHeaders() 属于 UrlRequestJob。
            headers = info.httpHeaders()
        except Exception:
            log.exception("读取内置登录请求头失败：%s", url.toString())
            return
        for key, value in headers.items():
            key_text = key.decode("utf-8", errors="replace") if isinstance(key, bytes) else str(key)
            if key_text.lower() != "cookie":
                continue
            cookie_text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
            self.owner._on_request_cookie(cookie_text, url.host())
            break


class _Task(QRunnable):
    """通用后台任务。"""

    def __init__(self, fn, on_done, task_name: str = ""):
        super().__init__()
        self.fn = fn
        self.on_done = on_done
        self.task_name = task_name

    def run(self) -> None:
        try:
            result = self.fn()
        except Exception as e:
            # 记录完整异常（含 traceback）到日志，便于排查"未知错误"
            log.exception("[后台任务] %s 执行异常", self.task_name or "未知任务")
            result = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        self.on_done(result)


class Bridge(QObject):
    """全局桥接对象（注册为 QML 上下文属性 `Bridge`）。"""

    # 信号（QML 可监听）
    searchDone = Signal(str, "QVariantMap")  # (platform, results)
    albumLoaded = Signal("QVariantMap")    # 专辑详情
    playUrlReady = Signal("QVariantMap")  # 播放地址及错误结果
    downloadProgress = Signal(int, int, int)  # (index, done, total)
    downloadDone = Signal(int, str)       # (index, status)
    lrtsTrackStatus = Signal(str, str)    # (section, status)
    loginStatus = Signal(str)             # 登录状态
    directoryChosen = Signal(str)         # 目录选择结果
    message = Signal(str, str)            # (title, content)
    playerPositionChanged = Signal(int)
    playerDurationChanged = Signal(int)
    playerStateChanged = Signal(str)
    playerError = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._player.positionChanged.connect(
            lambda value: self.playerPositionChanged.emit(int(value))
        )
        self._player.durationChanged.connect(
            lambda value: self.playerDurationChanged.emit(int(value))
        )
        self._player.playbackStateChanged.connect(self._on_player_state_changed)
        self._player.errorOccurred.connect(self._on_player_error)
        self.playUrlReady.connect(self._on_play_url_ready)
        self._lrts = None
        self._ximalaya = None
        self._qidian = None
        self._cookie = ""
        self._lrts_mode = "app"      # 默认移动 App 模式
        self._lrts_auth: dict = {}   # App 端签名参数
        self._download_tasks: dict[int, Any] = {}
        self._webengine_app = None
        self._login_window = None
        self._login_profile = None
        self._login_view = None
        self._login_status = None
        self._login_cookies: dict[str, str] = {}
        self._login_cookie_attempts = 0
        self._login_interceptor = None
        self._qidian_login_window = None
        self._qidian_login_profile = None
        self._qidian_login_cookies: dict[str, str] = {}
        self._playing_quality = 1
        self._search_cache: dict[tuple[str, str], dict] = {}
        try:
            from app.core.settings import AppSettings
            saved_cache = AppSettings.get("SearchCache", "") or ""
            for key, value in json.loads(saved_cache).items():
                platform, query = key.split("\u001f", 1)
                self._search_cache[(platform, query)] = value
        except Exception:
            pass

    def _save_search_cache(self) -> None:
        try:
            from app.core.settings import AppSettings
            data = {f"{p}\u001f{q}": value for (p, q), value in self._search_cache.items()}
            AppSettings.set("SearchCache", json.dumps(data, ensure_ascii=False))
        except Exception as exc:
            log.warning("保存搜索缓存失败：%s", exc)

    @Slot("QVariantMap")
    def _on_play_url_ready(self, result: dict) -> None:
        if not result.get("ok"):
            return
        url = result.get("url", "")
        if not url:
            self.playerError.emit("服务器未返回有效播放地址")
            return
        self._player.setSource(QUrl(url))
        self._player.play()

    @Slot(object)
    def _on_player_state_changed(self, state) -> None:
        if state == QMediaPlayer.PlayingState:
            value = "playing"
        elif state == QMediaPlayer.PausedState:
            value = "paused"
        else:
            value = "stopped"
        self.playerStateChanged.emit(value)

    @Slot(object, str)
    def _on_player_error(self, error, error_string: str) -> None:
        if error != QMediaPlayer.NoError:
            log.error("音频播放失败：%s", error_string)
            detail = error_string or "音频播放失败"
            if self._playing_quality >= 2:
                detail += (
                    "；当前为高清/极致音质，通常是 MGG 加密音频解密或播放器兼容失败。"
                    "可能原因：App 认证参数或 ekey 已过期、播放地址已失效，"
                    "或当前 Qt FFmpeg 不支持该 MGG 封装。请刷新 App 认证后重试，"
                    "仍失败时切换为标准音质。"
                )
            self.playerError.emit(detail)

    @Slot()
    def player_play(self) -> None:
        self._player.play()

    @Slot()
    def player_pause(self) -> None:
        self._player.pause()

    @Slot(float)
    def player_set_volume(self, value: float) -> None:
        self._audio_output.setVolume(max(0.0, min(float(value), 1.0)))

    @Slot()
    def set_webengine_application(self, app) -> None:
        """提供 QApplication，使内置登录窗口复用当前 Qt 应用。"""
        self._webengine_app = app

    @staticmethod
    def _cookie_parts(cookie_text: str) -> dict[str, str]:
        """解析浏览器/抓包复制的 Cookie 文本，忽略 Cookie: 前缀和换行。"""
        text = (cookie_text or "").strip()
        if text.lower().startswith("cookie:"):
            text = text[7:].strip()
        parts = {}
        for item in text.replace("\r", ";").replace("\n", ";").split(";"):
            if "=" not in item:
                continue
            name, value = item.strip().split("=", 1)
            if name and value:
                parts[name.strip()] = value.strip()
        return parts

    def _has_lrts_login_cookies(self) -> bool:
        """匹配 H5/小程序实际使用的会话字段，而非假设固定字段名。"""
        names = set(self._login_cookies)
        return (
            "token" in names
            and bool(names & {"user_id", "uid"})
            and bool(names & {"lrts_mobile_login_session", "sid"})
        )

    def _apply_webengine_cookies(self) -> None:
        if not self._login_cookies:
            return
        cookie = "; ".join(
            f"{name}={value}" for name, value in self._login_cookies.items()
        )
        self.set_cookie(cookie)
        self.loginStatus.emit("内置登录会话已应用，可点击检测登录状态")

    @Slot()
    def open_embedded_login(self) -> None:
        """打开内置登录页，并在登录后自动同步 m.lrts.me Cookie。"""
        if self._login_window is not None:
            self._login_window.show()
            self._login_window.raise_()
            self._login_window.activateWindow()
            return
        self._login_cookies = {}
        self._login_cookie_attempts = 0
        from app.core.settings import AppSettings
        profile_dir = AppSettings.get("LRTSWebEngineProfile", "") or ""
        if not profile_dir:
            import os
            profile_dir = os.path.join(os.path.expanduser("~"), ".audiobook-downloader", "lrts-webengine")
            AppSettings.set("LRTSWebEngineProfile", profile_dir)
        import os
        os.makedirs(profile_dir, exist_ok=True)
        self._login_profile = QWebEngineProfile("lrts-login", self)
        self._login_interceptor = _LoginRequestInterceptor(self)
        self._login_profile.setUrlRequestInterceptor(self._login_interceptor)
        self._login_profile.setPersistentStoragePath(profile_dir)
        self._login_profile.setCachePath(os.path.join(profile_dir, "cache"))
        self._login_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self._login_profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
        self._login_profile.cookieStore().cookieAdded.connect(self._on_login_cookie)
        view = QWebEngineView()
        view.setPage(_LoginPage(self._login_profile, view))
        # 懒人听书播放器返回 HTTP 音频地址；允许在 HTTPS 页面中加载该媒体。
        settings = view.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.AllowGeolocationOnInsecureOrigins, True
        )
        view.loadStarted.connect(lambda: self._set_login_status("正在加载登录页..."))
        view.loadProgress.connect(lambda value: self._set_login_status(f"正在加载登录页... {value}%"))
        view.loadFinished.connect(self._on_login_load_finished)
        view.urlChanged.connect(self._on_login_url_changed)
        view.page().profile().cookieStore().cookieAdded.connect(self._on_login_cookie)
        view.renderProcessTerminated.connect(self._on_login_render_terminated)
        view.page().javaScriptConsoleMessage = self._on_login_js_message
        # 归档插件使用 HTTP 移动 H5 入口；该入口才会建立移动端会话字段。
        login_url = "http://m.lrts.me/login?redirectUrl=%2Fuser"
        view.setUrl(QUrl(login_url))
        window = QMainWindow()
        window.setWindowTitle("懒人听书内置登录")
        window.setMinimumSize(320, 568)
        # 移动端 H5 使用 9:16 竖屏比例，并按当前屏幕可用区域自适应。
        screen = window.screen() or self._webengine_app.primaryScreen()
        available = screen.availableGeometry()
        margin = 48
        max_width = min(480, available.width() - margin)
        max_height = available.height() - margin
        width = max(320, max_width)
        height = int(width * 16 / 9)
        if height > max_height:
            height = max_height
            width = int(height * 9 / 16)
        window.resize(width, height)
        container = QWidget(window)
        layout = QVBoxLayout(container)
        status = QLabel("准备加载登录页...")
        status.setMinimumHeight(28)
        layout.addWidget(status)
        layout.addWidget(view, 1)
        window.setCentralWidget(container)
        window.destroyed.connect(self._on_login_window_closed)
        self._login_window = window
        self._login_view = view
        self._login_status = status
        window.show()

    def _set_login_status(self, text: str) -> None:
        if self._login_status is not None:
            self._login_status.setText(text)

    def _on_login_url_changed(self, url: QUrl) -> None:
        text = url.toString()
        if url.scheme() == "lazyaudio":
            self._set_login_status("检测到懒人听书 App 唤起请求，已留在内置页面")
            log.info("拦截懒人听书 App 唤起：%s", text.split("?", 1)[0])
            return
        if url.host() == "apps.apple.com" or url.host() == "play.google.com":
            self._set_login_status("已阻止跳转应用商店，登录窗口仍可使用")
            return
        self._set_login_status(f"页面：{text}")
        if url.host().endswith("lrts.me") and url.path() in ("/user", "/"):
            self._set_login_status("登录成功，正在同步会话...")
            QTimer.singleShot(1200, self._refresh_login_cookies)

    def _refresh_login_cookies(self) -> None:
        if self._login_profile is None:
            return
        # 主动读取现有 Cookie，不清理会话，避免把刚完成的登录注销。
        self._login_cookie_attempts = 0
        self._login_profile.cookieStore().loadAllCookies()
        if self._login_view is not None:
            self._login_view.page().runJavaScript(
                "fetch('/ajax/getUserInfo', {credentials: 'include'}).then(() => document.cookie).catch(() => document.cookie)",
                self._on_document_cookie,
            )
        QTimer.singleShot(1500, self._collect_login_cookies)

    def _on_request_cookie(self, cookie_text: str, host: str) -> None:
        self._login_cookies.update(self._cookie_parts(cookie_text))
        log.info("内置登录请求 Cookie 已读取：host=%s names=%s", host, ", ".join(sorted(self._login_cookies)))
        if self._has_lrts_login_cookies():
            self._apply_webengine_cookies()

    def _on_document_cookie(self, cookie_text: str) -> None:
        self._login_cookies.update(self._cookie_parts(cookie_text))
        if self._login_cookies:
            log.info("内置登录 document.cookie 已读取：%s", ", ".join(sorted(self._login_cookies)))

    def _collect_login_cookies(self) -> None:
        self._login_cookie_attempts += 1
        if self._has_lrts_login_cookies():
            names = sorted(self._login_cookies)
            log.info("内置登录 Cookie 已捕获：%s", ", ".join(names))
            self._apply_webengine_cookies()
            self._set_login_status("会话已同步，可返回主界面检测登录状态")
            return
        if self._login_cookie_attempts < 6 and self._login_profile is not None:
            self._login_profile.cookieStore().loadAllCookies()
            self._login_view.page().runJavaScript(
                "document.cookie", self._on_document_cookie
            )
            self._set_login_status(
                f"正在同步登录会话... ({self._login_cookie_attempts}/5)"
            )
            QTimer.singleShot(1500, self._collect_login_cookies)
            return
        self._set_login_status("未捕获到登录会话 Cookie，请在内置窗口完成登录后重试")
        log.warning("内置登录 Cookie 收集失败：未收到有效 lrts.me 登录会话")

    def _on_login_load_finished(self, ok: bool) -> None:
        if ok:
            self._set_login_status(f"页面加载完成：{self._login_view.url().toString()}")
            log.info("内置登录页加载完成：%s", self._login_view.url().toString())
        else:
            self._set_login_status("登录页加载失败，请检查网络或代理")
            log.error("内置登录页加载失败：%s", self._login_view.url().toString())

    def _on_login_render_terminated(self, status, exit_code) -> None:
        self._set_login_status(f"网页渲染进程异常退出：{status} / {exit_code}")
        log.error("内置登录渲染进程退出：status=%s exit_code=%s", status, exit_code)

    def _on_login_js_message(self, level, message, line, source_id) -> None:
        log.warning("内置登录 JavaScript：%s:%s %s", source_id, line, message)

    def _on_login_cookie(self, cookie) -> None:
        domain = cookie.domain().lstrip(".")
        name = bytes(cookie.name()).decode("utf-8", errors="replace")
        value = bytes(cookie.value()).decode("utf-8", errors="replace")
        log.info("内置登录 CookieStore：domain=%s name=%s secure=%s httpOnly=%s", domain, name, cookie.isSecure(), cookie.isHttpOnly())
        if domain in ("lrts.me", "m.lrts.me") or domain.endswith(".lrts.me"):
            self._login_cookies[name] = value
            if self._has_lrts_login_cookies():
                self._apply_webengine_cookies()

    def _on_login_window_closed(self) -> None:
        self._login_window = None
        self._login_profile = None

    # ------------------------------------------------------------------ #
    # 懒人听书
    # ------------------------------------------------------------------ #
    def _ensure_lrts(self):
        if self._lrts is None:
            from app.core.lrts_api import LRTSClient
            # 从设置恢复 Cookie 与模式
            try:
                from app.core.settings import AppSettings
                if not self._cookie:
                    self._cookie = AppSettings.cookie() or ""
                saved_mode = AppSettings.get("LRTSMode", "app") or "app"
                self._lrts_mode = saved_mode
                saved_auth = AppSettings.get("LRTSAuth", "") or ""
                if saved_auth:
                    import json as _json
                    self._lrts_auth = _json.loads(saved_auth) if isinstance(saved_auth, str) else dict(saved_auth)
            except Exception as e:
                log.warning("恢复懒人听书登录参数失败：%s", e)
            self._lrts = LRTSClient(cookie=self._cookie, mode=self._lrts_mode,
                                    auth=self._lrts_auth)

    @Slot(str)
    def search_lrts(self, keyword: str) -> None:
        self._ensure_lrts()
        cache_key = ("lrts", keyword.strip().lower())
        cached = self._search_cache.get(cache_key)
        if cached is not None:
            self.searchDone.emit("lrts", dict(cached, cached=True))
            return

        def fn():
            data = self._lrts.search(keyword)
            d = data.get("data") or {}
            br = d.get("bookResult") or {}
            ar = d.get("announcerResult") or {}
            return {"ok": True, "books": br.get("list") or [], "anchors": ar.get("list") or []}

        def done(r):
            if r.get("ok"):
                self._search_cache[cache_key] = dict(r)
                self._save_search_cache()
            self.searchDone.emit("lrts", r)

        self._pool.start(_Task(fn, done, task_name="lrts.search"))

    @Slot(str)
    def refresh_search_lrts(self, keyword: str) -> None:
        self._search_cache.pop(("lrts", keyword.strip().lower()), None)
        self._save_search_cache()
        self.search_lrts(keyword)

    @Slot(str)
    def load_album_lrts(self, book_id: str) -> None:
        self._ensure_lrts()
        cache_key = ("lrts_album", str(book_id).strip())
        cached = self._search_cache.get(cache_key)
        if cached is not None and cached.get("ok") and cached.get("tracks"):
            cached_result = dict(cached, cached=True)
            cached_result["tracks"] = list(cached.get("tracks") or [])[:60]
            self._pool.start(_Task(
                lambda: cached_result,
                lambda result: self.albumLoaded.emit(result),
                task_name="lrts.cached_album",
            ))
            return

        def fn():
            detail = self._lrts.album_detail(book_id)
            d = detail.get("data") or {}
            album = d.get("bookDetail") or {}
            menu = self._lrts.album_menu(book_id, page=1, page_size=60)
            tracks = menu.get("list") or []
            # 首次只加载第一页；用户点击“加载全部”时再获取其余分页。
            total = menu.get("sections", 0)
            # 统一字段：id=resId, tmeId=trackId, section=集数
            norm = []
            for t in tracks:
                norm.append({
                    "id": t.get("id") or t.get("sectionId"),
                    "sectionId": t.get("sectionId"),
                    "section": t.get("section"),
                    "tmeId": t.get("tmeId"),
                    "name": t.get("name"),
                    "title": t.get("name"),
                    "length": t.get("length"),
                    "size": t.get("size"),
                    "hqMedias": t.get("hqMedias"),
                })
            return {"ok": True, "album": album, "albumId": str(book_id), "tracks": norm}

        def done(r):
            if r.get("ok"):
                self._search_cache[cache_key] = dict(r)
                self._save_search_cache()
            self.albumLoaded.emit(r)

        self._pool.start(_Task(fn, done, task_name="lrts.load_album"))

    @Slot(str)
    def load_all_album_lrts(self, book_id: str) -> None:
        self._ensure_lrts()
        def fn():
            tracks = []
            page = 1
            while True:
                menu = self._lrts.album_menu(book_id, page=page, page_size=60)
                items = menu.get("list") or []
                if not items:
                    break
                tracks.extend(items)
                total = menu.get("sections", 0)
                if len(items) < 60 or (total and len(tracks) >= total):
                    break
                page += 1
            norm = [{"id": t.get("id") or t.get("sectionId"), "sectionId": t.get("sectionId"), "section": t.get("section"), "tmeId": t.get("tmeId"), "name": t.get("name"), "title": t.get("name"), "length": t.get("length"), "size": t.get("size"), "hqMedias": t.get("hqMedias")} for t in tracks]
            cached = self._search_cache.get(("lrts_album", str(book_id).strip()), {})
            return {"ok": True, "album": cached.get("album", {}), "albumId": str(book_id), "tracks": norm}
        def done(r):
            if r.get("ok"):
                self._search_cache[("lrts_album", str(book_id).strip())] = dict(r)
                self._save_search_cache()
            self.albumLoaded.emit(r)
        self._pool.start(_Task(fn, done, task_name="lrts.load_all_album"))

    @Slot(str, str, str, str, int)
    def get_play_url_lrts(self, track_id: str, res_id: str, section: str,
                          album_id: str, quality: int = 3) -> None:
        self._ensure_lrts()
        self._playing_quality = max(1, min(int(quality), 3))

        def fn():
            if self._lrts_mode == "app":
                request_section = {
                    "section": int(section),
                    "resId": str(res_id),
                    "trackId": str(track_id),
                }
                paths = self._lrts.app_batch_listen_path(
                    album_id, [request_section], quality
                )
                if paths and paths[0].get("path"):
                    return {"ok": True, "url": paths[0]["path"],
                            "quality": paths[0].get("quality", quality)}
                raise RuntimeError("该章节没有可用的音质播放地址")
            url = self._lrts.get_listen_path(track_id, album_id, 1, quality)
            return {"ok": True, "url": url, "quality": quality}

        def done(r):
            error_text = str(r.get("error", ""))
            if not r.get("ok"):
                if "status=118" in error_text or "请验证" in error_text:
                    r["error"] = (
                        "服务端返回 118：需要验证（这不等同于 Token 已过期）。"
                        "请前往懒人听书 App 完成验证；验证后重新获取并应用 App 认证参数，再重新播放。"
                    )
                    self.loginStatus.emit(r["error"])
                elif any(word in error_text.lower() for word in ("token expired", "token 过期", "token失效", "令牌过期")):
                    r["error"] = (
                        "Token 已过期或失效，请前往懒人听书 App 重新认证，"
                        "再重新获取并应用 App 认证参数。"
                    )
                    self.loginStatus.emit(r["error"])
            if not r.get("ok") and self._playing_quality >= 2:
                r["error"] = (
                    r.get("error", "获取播放地址失败")
                    + "；当前为高清/极致音质，可能是 MGG 加密音频解密失败、"
                    "ekey/认证参数过期、播放地址失效或 Qt FFmpeg 不兼容。"
                    "请刷新 App 认证，或切换为标准音质。"
                )
            self.playUrlReady.emit(r)

        self._pool.start(_Task(fn, done, task_name="lrts.get_play_url"))

    @Slot(str, str, int, str, str)
    def download_batch_lrts(self, book_id: str, sections_json: str,
                            quality: int = 1, save_dir: str = "",
                            album_title: str = "") -> None:
        """
        懒人听书批量下载（App 端 batchGetListenPath 接口）。
        sections_json: JSON 数组 [{"section":1,"resId":"...","trackId":"...","name":"..."}]
        """
        self._ensure_lrts()

        requested_save_dir = save_dir

        def fn():
            import json as _json
            import os
            from app.core.downloader import DownloadTask

            if self._lrts_mode != "app":
                return {"ok": False, "error": "批量下载需要 App 登录模式（已切换模式？）"}

            sections = _json.loads(sections_json)
            sections = [{
                "section": int(s.get("section", 0)),
                "resId": str(s.get("resId") or s.get("id") or s.get("sectionId") or ""),
                "trackId": str(s.get("trackId") or s.get("tmeId") or s.get("id") or ""),
                "name": str(s.get("name") or s.get("title") or ""),
            } for s in sections]
            if not sections:
                return {"ok": False, "error": "章节列表为空"}
            if any(not s["resId"] or not s["trackId"] for s in sections):
                return {"ok": False, "error": "章节数据缺少音频标识，请刷新专辑后重试"}

            download_dir = requested_save_dir
            if not download_dir:
                from app.core.settings import AppSettings
                download_dir = AppSettings.save_dir()
            if not download_dir:
                download_dir = os.path.join(os.path.expanduser("~"), "Music", "有声书")
            folder_name = album_title.strip() or str(book_id).strip() or "未命名专辑"
            for char in '<>:"/\\|?*':
                folder_name = folder_name.replace(char, "_")
            folder_name = folder_name.rstrip(". ") or "未命名专辑"
            download_dir = os.path.join(download_dir, folder_name)
            os.makedirs(download_dir, exist_ok=True)

            results = []
            total = len(sections)
            for i in range(0, total, 5):
                batch = sections[i:i + 5]
                pending = []
                for section in batch:
                    prefix = f"{int(section['section']):04d}"
                    name = section.get("name", "")
                    candidates = [
                        entry for entry in os.listdir(download_dir)
                        if entry.startswith(prefix) and (not name or name in entry)
                    ]
                    existing = next(
                        (entry for entry in candidates
                         if os.path.isfile(os.path.join(download_dir, entry))
                         and os.path.getsize(os.path.join(download_dir, entry)) > 0),
                        None,
                    )
                    if existing:
                        self.lrtsTrackStatus.emit(str(section["section"]), "已完成")
                        results.append({"ok": True, "section": section["section"], "status": "已存在"})
                    else:
                        self.lrtsTrackStatus.emit(str(section["section"]), "下载中")
                        pending.append(section)
                if not pending:
                    continue
                batch = pending
                try:
                    paths = self._lrts.app_batch_listen_path(book_id, batch, quality)
                except Exception as e:
                    log.warning("[批量下载] 第 %d 批获取地址失败：%s", i // 5 + 1, e)
                    for section in batch:
                        self.lrtsTrackStatus.emit(str(section["section"]), "无权限")
                    results.append({"ok": False, "error": f"批量获取地址失败：{e}"})
                    continue
                for p in paths:
                    sec = next((s for s in batch if s["section"] == p["section"]), {})
                    name = sec.get("name", "")
                    ext = ".mgg" if p.get("ekey") else (".m4a" if ".m4a" in p["path"] else ".mp3")
                    fname = f"{p['section']:>04d} {name}{ext}" if name else f"{p['section']:>04d}{ext}"
                    dest = os.path.join(download_dir, fname)
                    if os.path.exists(dest) and os.path.getsize(dest) > 0:
                        self.lrtsTrackStatus.emit(str(p["section"]), "已完成")
                        results.append({"ok": True, "section": p["section"], "status": "已存在"})
                        continue
                    task = DownloadTask(p["path"], dest, progress_cb=None)
                    task.run()
                    ok = os.path.exists(dest)
                    self.lrtsTrackStatus.emit(str(p["section"]), "已完成" if ok else "无权限")
                    results.append({
                        "ok": ok,
                        "section": p["section"],
                        "status": "完成" if ok else "失败",
                        "ekey": p.get("ekey", ""),
                    })
            ok_n = sum(1 for r in results if r.get("ok"))
            return {"ok": True, "done": ok_n, "total": total, "results": results}

        def done(r):
            quality_name = {1: "标准", 2: "高清", 3: "极致"}.get(int(quality), "标准")
            if r.get("ok"):
                detail = r.get("results") or []
                ok_n = sum(1 for x in detail if x.get("ok"))
                msg = f"批量下载完成：{ok_n}/{r.get('total', 0)} 集（{quality_name}音质）"
                failed = [x for x in detail if not x.get("ok")]
                if failed:
                    msg += "；失败集数：" + ", ".join(str(x.get("section", "?")) for x in failed[:8])
                    if int(quality) >= 2:
                        msg += "。高清/极致音频可能为 MGG 加密格式，当前未能解密或下载地址已失效；请刷新 App 认证或改用标准音质。"
                self.message.emit("批量下载", msg)
            else:
                msg = r.get("error", "未知错误")
                if int(quality) >= 2:
                    msg += "；高清/极致音频可能涉及 MGG 加密、ekey 过期或认证失效，建议刷新 App 认证或改用标准音质。"
                self.message.emit("批量下载", msg)

        self._pool.start(_Task(fn, done, task_name="lrts.batch_download"))

    # ------------------------------------------------------------------ #
    # 喜马拉雅
    # ------------------------------------------------------------------ #
    def _ensure_ximalaya(self):
        if self._ximalaya is None:
            from app.core.ximalaya_api import XimalayaClient
            self._ximalaya = XimalayaClient()

    @Slot(str)
    def parse_ximalaya_album(self, url_or_id: str) -> None:
        """输入专辑网址或 ID，优先使用缓存解析结果。"""
        self._ensure_ximalaya()
        cache_key = ("ximalaya", url_or_id.strip().lower())
        cached = self._search_cache.get(cache_key)
        if cached is not None:
            self.albumLoaded.emit(dict(cached, cached=True))
            return

        def fn():
            return self._ximalaya.parse_album(url_or_id)

        def done(r):
            if r.get("ok"):
                self._search_cache[cache_key] = dict(r)
                self._save_search_cache()
            self.albumLoaded.emit(r)

        self._pool.start(_Task(fn, done, task_name="ximalaya.parse_album"))

    @Slot(str)
    def refresh_ximalaya_album(self, url_or_id: str) -> None:
        self._search_cache.pop(("ximalaya", url_or_id.strip().lower()), None)
        self._save_search_cache()
        self.parse_ximalaya_album(url_or_id)

    @Slot(str, int)
    def get_track_url_ximalaya(self, track_id: str, quality: int = 1) -> None:
        """获取喜马拉雅单曲真实播放地址（含解密）。"""
        self._ensure_ximalaya()

        def fn():
            url = self._ximalaya.get_track_url(track_id, quality)
            return {"ok": True, "url": url}

        def done(r):
            self.playUrlReady.emit(r)

        self._pool.start(_Task(fn, done, task_name="ximalaya.track_url"))

    def _ensure_qidian(self):
        if self._qidian is None:
            from app.core.qidian_api import QidianClient
            try:
                from app.core.settings import AppSettings
                cookie = AppSettings.get("QidianCookie", "") or ""
            except Exception:
                cookie = ""
            self._qidian = QidianClient(cookie=cookie)

    @Slot(result=str)
    def get_qidian_cookie(self) -> str:
        if self._qidian is not None:
            return self._qidian.session.headers.get("Cookie", "")
        try:
            from app.core.settings import AppSettings
            return AppSettings.get("QidianCookie", "") or ""
        except Exception as e:
            log.warning("读取起点 Cookie 失败：%s", e)
            return ""

    @Slot(str)
    def set_qidian_cookie(self, cookie: str) -> None:
        """应用并保存起点站点 Cookie；起点不接受懒人听书的认证参数。"""
        normalized = "; ".join(
            f"{name}={value}" for name, value in self._cookie_parts(cookie).items()
        )
        self._ensure_qidian()
        self._qidian.set_cookie(normalized)
        try:
            from app.core.settings import AppSettings
            AppSettings.set("QidianCookie", normalized)
        except Exception as e:
            log.warning("保存起点 Cookie 失败：%s", e)
        self.loginStatus.emit("起点 Cookie 已应用并保存，可点击检测登录状态")

    @Slot()
    def check_qidian_login_status(self) -> None:
        """检查起点 Cookie 是否已配置；账号权限仍需以实际播放结果为准。"""
        self._ensure_qidian()

        def fn():
            cookie = self._qidian.session.headers.get("Cookie", "")
            if not cookie:
                return {"ok": False, "error": "尚未应用起点 Cookie"}
            return {"ok": True, "count": len(self._cookie_parts(cookie))}

        def done(result):
            if result.get("ok"):
                self.loginStatus.emit(
                    f"已配置起点 Cookie（{result.get('count', 0)} 项）；账号及章节权限以实际播放结果为准"
                )
            else:
                self.loginStatus.emit(f"起点登录检测失败：{result.get('error', '')}")

        self._pool.start(_Task(fn, done, task_name="qidian.check_login"))

    # ------------------------------------------------------------------ #
    # 起点
    # ------------------------------------------------------------------ #
    @Slot(str)
    def search_qidian(self, keyword: str) -> None:
        self._ensure_qidian()
        cache_key = ("qidian", keyword.strip().lower())
        cached = self._search_cache.get(cache_key)
        if cached is not None:
            self.searchDone.emit("qidian", dict(cached, cached=True))
            return

        def fn():
            data = self._qidian.search(keyword)
            return {"ok": True, "books": data}

        def done(r):
            if r.get("ok"):
                self._search_cache[cache_key] = dict(r)
                self._save_search_cache()
            self.searchDone.emit("qidian", r)

        self._pool.start(_Task(fn, done, task_name="qidian.search"))

    @Slot(str)
    def refresh_search_qidian(self, keyword: str) -> None:
        self._search_cache.pop(("qidian", keyword.strip().lower()), None)
        self._save_search_cache()
        self.search_qidian(keyword)

    @Slot(str)
    def load_book_qidian(self, adid: str) -> None:
        self._ensure_qidian()
        cache_key = ("qidian_book", str(adid).strip())
        cached = self._search_cache.get(cache_key)
        if cached is not None:
            self.albumLoaded.emit(dict(cached, cached=True))
            return

        def fn():
            detail = self._qidian.book_detail(adid)
            chapters = self._qidian.chapter_list(adid)
            return {"ok": True, "book": detail, "chapters": chapters}

        def done(r):
            if r.get("ok"):
                self._search_cache[cache_key] = dict(r)
                self._save_search_cache()
            self.albumLoaded.emit(r)

        self._pool.start(_Task(fn, done, task_name="qidian.load_book"))

    @Slot(str, str)
    def get_play_url_qidian(self, adid: str, acid: str) -> None:
        self._ensure_qidian()

        def fn():
            url = self._qidian.play_url(adid, acid)
            return {"ok": True, "url": url}

        def done(r):
            self.playUrlReady.emit(r)

        self._pool.start(_Task(fn, done, task_name="qidian.play_url"))

    # ------------------------------------------------------------------ #
    # 下载
    # ------------------------------------------------------------------ #
    @Slot(str, str, int)
    def download(self, url: str, dest: str, index: int) -> None:
        from app.core.downloader import DownloadTask

        def fn():
            task = DownloadTask(
                url, dest,
                progress_cb=lambda d, t: self.downloadProgress.emit(index, d, t),
                done_cb=lambda ok, msg: self.downloadDone.emit(index, "完成" if ok else f"失败:{msg}"),
            )
            task.run()
            return {"ok": True}

        self._pool.start(_Task(fn, lambda r: None, task_name=f"download[{index}]"))

    # ------------------------------------------------------------------ #
    # 登录
    # ------------------------------------------------------------------ #
    @Slot(str)
    def set_lrts_mode(self, mode: str) -> None:
        """设置并持久化懒人听书登录模式：web / wechat / app。"""
        self._ensure_lrts()
        self._lrts_mode = mode
        from app.core.lrts_api import LRTSClient
        self._lrts = LRTSClient(cookie=self._cookie, mode=mode, auth=self._lrts_auth)
        try:
            from app.core.settings import AppSettings
            AppSettings.set("LRTSMode", mode)
        except Exception as e:
            log.warning("保存懒人听书模式失败：%s", e)
        mode_names = {"app": "APP（移动端）", "wechat": "微信", "web": "网页"}
        self.loginStatus.emit(f"已切换懒人听书登录模式：{mode_names.get(mode, mode)}")

    @Slot(result=str)
    def get_lrts_auth(self) -> str:
        import json as _json
        try:
            from app.core.settings import AppSettings
            saved = AppSettings.get("LRTSAuth", "") or ""
            if isinstance(saved, str):
                try:
                    return _json.dumps(_json.loads(saved), ensure_ascii=False, indent=2)
                except Exception:
                    return saved
            return _json.dumps(saved, ensure_ascii=False, indent=2)
        except Exception as e:
            log.warning("读取 App 认证参数失败：%s", e)
            return ""

    @Slot(str)
    def set_lrts_auth(self, auth_json: str) -> None:
        """设置 App 端签名参数（从 ProxyPin 抓包获取的 JSON）。"""
        import json as _json
        try:
            auth = _json.loads(auth_json)
        except Exception as e:
            self.loginStatus.emit(f"签名参数解析失败：{e}")
            return
        if not isinstance(auth, dict) or not auth.get("token"):
            self.loginStatus.emit("App 认证参数缺少 token")
            return
        self._lrts_auth = auth
        self._lrts_mode = "app"
        if self._lrts:
            self._lrts.set_auth(auth)
            self._lrts.mode = "app"
            self._lrts.session.headers.clear()
        try:
            from app.core.settings import AppSettings
            AppSettings.set("LRTSAuth", _json.dumps(auth, ensure_ascii=False))
            AppSettings.set("LRTSMode", "app")
        except Exception as e:
            log.warning("保存 App 认证参数失败：%s", e)
        self.loginStatus.emit("App 端签名参数已应用并保存")

    @Slot()
    def open_wechat_login(self) -> None:
        """在内置 WebEngine 中打开微信小程序对应的 H5 登录入口。"""
        self.open_embedded_login()

    @Slot()
    def open_web_login(self) -> None:
        """在内置 WebEngine 中登录并自动同步 m.lrts.me 会话。"""
        self.open_embedded_login()

    @Slot()
    def open_ximalaya_login(self) -> None:
        """打开喜马拉雅扫码登录页。"""
        import webbrowser
        webbrowser.open("https://passport.ximalaya.com/web/qrCode/gen?level=L")

    @Slot()
    def open_qidian_login(self) -> None:
        """打开起点内置扫码登录页，并自动同步起点域名 Cookie。"""
        if self._qidian_login_window is not None:
            self._qidian_login_window.show()
            self._qidian_login_window.raise_()
            self._qidian_login_window.activateWindow()
            return
        if self._webengine_app is None:
            self.loginStatus.emit("内置浏览器尚未初始化")
            return

        import os
        from app.core.settings import AppSettings
        profile_dir = AppSettings.get("QidianWebEngineProfile", "") or ""
        if not profile_dir:
            profile_dir = os.path.join(
                os.path.expanduser("~"), ".audiobook-downloader", "qidian-webengine"
            )
            AppSettings.set("QidianWebEngineProfile", profile_dir)
        os.makedirs(profile_dir, exist_ok=True)

        profile = QWebEngineProfile("qidian-login", self)
        profile.setPersistentStoragePath(profile_dir)
        profile.setCachePath(os.path.join(profile_dir, "cache"))
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
        profile.cookieStore().cookieAdded.connect(self._on_qidian_login_cookie)
        view = QWebEngineView()
        view.setPage(_LoginPage(profile, view))
        view.load(QUrl("https://my.qidian.com/?ticket="))
        window = QMainWindow()
        window.setWindowTitle("起点扫码登录")
        window.resize(900, 680)
        container = QWidget(window)
        layout = QVBoxLayout(container)
        status = QLabel("请在起点页面完成扫码登录，Cookie 将自动同步")
        status.setMinimumHeight(28)
        layout.addWidget(status)
        layout.addWidget(view, 1)
        window.setCentralWidget(container)
        window.destroyed.connect(self._on_qidian_login_window_closed)
        self._qidian_login_profile = profile
        self._qidian_login_window = window
        self._qidian_login_cookies = {}
        window.show()

    def _on_qidian_login_cookie(self, cookie) -> None:
        domain = cookie.domain().lstrip(".").lower()
        if domain != "qidian.com" and not domain.endswith(".qidian.com"):
            return
        name = bytes(cookie.name()).decode("utf-8", errors="replace")
        value = bytes(cookie.value()).decode("utf-8", errors="replace")
        self._qidian_login_cookies[name] = value
        cookie_text = "; ".join(
            f"{key}={val}" for key, val in self._qidian_login_cookies.items()
        )
        self.set_qidian_cookie(cookie_text)
        log.info("起点内置登录 Cookie 已同步：%s", ", ".join(sorted(self._qidian_login_cookies)))

    def _on_qidian_login_window_closed(self) -> None:
        self._qidian_login_window = None
        self._qidian_login_profile = None

    @Slot()
    def check_login_status(self) -> None:
        """检测当前程序已应用的会话；不会自动读取默认浏览器 Cookie。"""
        self._ensure_lrts()

        def fn():
            try:
                if self._lrts_mode == "app":
                    # App 模式：尝试拉一页章节列表验证签名
                    resp = self._lrts.app_chapter_list(68504304, page=1, page_size=1)
                    if resp.get("apiStatus") == 0 and resp.get("list"):
                        return {"ok": True, "nickname": "(App 签名)", "cookie": self._cookie}
                    return {"ok": False, "error": f"签名无效（apiStatus={resp.get('apiStatus')}）"}
                info = self._lrts.get_user_info()
                data = info.get("data") or {}
                if data.get("userId"):
                    return {"ok": True, "nickname": data.get("nickname", ""), "cookie": self._lrts.cookies}
                return {"ok": False, "error": f"会话无效（status={info.get('status')}，请重新登录并应用 Cookie）"}
            except Exception as e:
                log.warning("[登录检测] 异常：%s", e)
                return {"ok": False, "error": f"{type(e).__name__}: {e}"}

        def done(r):
            if r.get("ok"):
                self._cookie = r.get("cookie", self._cookie)
                self.loginStatus.emit(f"登录成功：{r.get('nickname', '')}")
            else:
                self.loginStatus.emit(f"尚未检测到登录：{r.get('error', '')}")

        self._pool.start(_Task(fn, done, task_name="lrts.check_login"))

    @Slot()
    def choose_directory(self) -> None:
        """选择目录（QML 回调）。"""
        from PySide6.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(None, "选择保存目录")
        if path:
            self.directoryChosen.emit(path)

    @Slot(str)
    def open_download_dir(self, album_title: str = "") -> None:
        """打开当前专辑下载目录；未选专辑时打开根目录。"""
        import os
        import subprocess
        from app.core.settings import AppSettings
        download_dir = AppSettings.save_dir()
        if not download_dir:
            download_dir = os.path.join(os.path.expanduser("~"), "Music", "有声书")
        if album_title.strip():
            folder_name = album_title.strip()
            for char in '<>:"/\\|?*':
                folder_name = folder_name.replace(char, "_")
            folder_name = folder_name.rstrip(". ") or "未命名专辑"
            download_dir = os.path.join(download_dir, folder_name)
        os.makedirs(download_dir, exist_ok=True)
        try:
            subprocess.Popen(["explorer", os.path.normpath(download_dir)])
        except Exception as e:
            log.warning("打开下载目录失败：%s", e)

    @Slot()
    def open_log_dir(self) -> None:
        """打开日志目录（资源管理器）。"""
        import os
        import subprocess
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "logs",
        )
        os.makedirs(log_dir, exist_ok=True)
        try:
            subprocess.Popen(["explorer", log_dir])
        except Exception as e:
            log.warning("打开日志目录失败：%s", e)

    @Slot(str)
    def set_cookie(self, cookie: str) -> None:
        cookie = "; ".join(
            f"{name}={value}" for name, value in self._cookie_parts(cookie).items()
        )
        self._cookie = cookie
        if self._lrts:
            self._lrts.set_cookie(cookie)
        # 持久化
        try:
            from app.core.settings import AppSettings
            AppSettings.set("UserCookie", cookie)
            AppSettings.set("LRTSMode", self._lrts_mode)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # 通用
    # ------------------------------------------------------------------ #
    @Slot()
    def show_message(self) -> None:
        pass
