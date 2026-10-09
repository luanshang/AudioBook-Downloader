# -*- coding: utf-8 -*-
"""
懒人听书 API 客户端（融合版）
=============================
支持三种登录方式与两套接口：

  ┌─────────────────────────────────────────────────────────────────────┐
  │ 登录方式         │ 接口域                     │ 特点                    │
  ├─────────────────┼────────────────────────────┼────────────────────────┤
  │ ① Web 端(H5)    │ m.lrts.me/ajax/*          │ 无需签名，Cookie 会话    │
  │ ② 微信小程序     │ m.lrts.me/ajax/*（微信UA） │ 无需签名，Cookie 会话    │
  │ ③ 移动端(App)   │ gzapi.mting.info/yyting/*  │ 需 token/sc 签名，批量  │
  └─────────────────┴────────────────────────────┴────────────────────────┘

核心接口（来自 ProxyPin 抓包逆向 + Web 插件 lrts-helper 反混淆）：

  Web 端（m.lrts.me/ajax/）：
    - search()            搜索
    - getBookDetail()     专辑详情
    - getBookMenu()       专辑目录（分页，每页 60，无需登录）
    - getListenPath()     单集播放/下载地址（需要登录 Cookie）
    - getUserInfo()       用户信息（登录态校验）

  App 端（gzapi.mting.info/yyting/）：
    - ClientGetBookResource.action  章节列表（分页，每页 50）
    - getResQualityEffectList       音质列表
    - batchGetListenPath            批量换播放地址（POST，支持 1~10 集/批）
    - getListenPath                 单集播放地址（GET）

音质（getResQualityEffectList 确认）：
    quality=1  标准 48kbps   明文 .m4a（可直接播放）
    quality=2  高清 192kbps  .mgg 加密（需 ekey，腾讯新版加密暂无公开解密）
    quality=3  极高 320kbps  .mgg 加密（同上）

用法：
    # Web 端 / 小程序（只需 Cookie）
    client = LRTSClient(mode="web", cookie="...")

    # App 端（需抓包签名参数）
    client = LRTSClient(mode="app", auth={
        "token": "...", "imei": "...", "lrid": "...", "sc": "...", ...
    })
"""

from __future__ import annotations

import json
import time
import urllib.parse

import requests

from app.core.logger import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------- 常量
WEB_BASE = "https://m.lrts.me"
APP_BASE = "https://shapi.mting.info/yyting"

# Web/H5 请求头：不要携带小程序专用标识。
WEB_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://m.lrts.me/",
}

# 微信小程序请求头
WECHAT_HEADERS = {
    "Accept": "application/json",
    "Host": "m.lrts.me",
    "X-Custom-Info": "weapp",
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0_1 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
        "MicroMessenger/8.0.53(0x1800352f) NetType/4G Language/zh_CN"
    ),
}

# 模拟 App 端请求头（vivo V2284A）
APP_HEADERS = {
    "User-Agent": "Android15/yyting/vivo/V2284A/ch_vivo/8823/Android",
    "Referer": "yytingting.com",
    "ClientVersion": "8.8.23",
    "Accept-Encoding": "gzip,deflate,sdch",
}

QUALITY_NAMES = {1: "标准48k", 2: "高清192k", 3: "极高320k"}


class LRTSClient:
    """懒人听书客户端（Web/小程序/App 三合一）。"""

    def __init__(self, cookie: str = "", mode: str = "web", auth: dict | None = None,
                 proxy: str = ""):
        """
        Args:
            cookie: 登录会话 Cookie（web / wechat 模式）
            mode:   "web"（H5网页）| "wechat"（微信小程序）| "app"（移动App）
            auth:   App 模式签名参数（token/imei/lrid/ostar36/duId/sc/q/ts/nonce）
            proxy:  可选代理，如 "http://127.0.0.1:7890"
        """
        self.mode = mode
        self.auth = auth or {}
        self.session = requests.Session()
        if cookie:
            self.session.headers["Cookie"] = cookie
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
            self.session.trust_env = False

    # ================================================================ #
    #  通用基础请求
    # ================================================================ #
    def _web_headers(self) -> dict:
        """Web 元数据接口始终使用浏览器/小程序协议头，App 模式也适用。"""
        if self.mode == "wechat":
            return dict(WECHAT_HEADERS)
        return dict(WEB_HEADERS)

    def _web_get(self, path: str, params: dict | None = None) -> dict:
        resp = self.session.get(
            WEB_BASE + path,
            params=params,
            headers=self._web_headers(),
            timeout=(10, 35),
        )
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            log.error("Web GET 失败 [%s] %s -> %s", resp.status_code, path, params)
            raise
        return resp.json()

    def _web_post(self, path: str, json: dict | None = None,
                  data: dict | None = None) -> dict:
        resp = self.session.post(
            WEB_BASE + path,
            json=json,
            data=data,
            headers=self._web_headers(),
            timeout=(10, 35),
        )
        resp.raise_for_status()
        return resp.json()

    # ---------------------------------------------------------------- #
    #  App 端签名请求（sc 绑定 ts/q/nonce，必须用抓包原值）
    # ---------------------------------------------------------------- #
    def _app_base(self) -> str:
        """返回抓包认证对应的 App API 基址。"""
        a = self.auth
        base = a.get("app_base") or a.get("base_url") or ""
        if not base and a.get("Host"):
            base = f"https://{a['Host'].strip()}/yyting"
        return (base or APP_BASE).rstrip("/")

    def _app_query(self, extra: dict | None = None) -> dict:
        a = self.auth
        q = {
            "token": a.get("token", ""),
            "imei": a.get("imei", ""),
            "nwt": str(a.get("nwt", "0")),
            "q": a.get("q", "2218"),
            "mode": "0",
            "lrid": a.get("lrid", ""),
            "ostar36": a.get("ostar36", ""),
            "ts": a.get("ts", str(int(time.time() * 1000))),
            "userMode": a.get("userMode", "1097865"),
            "duId": a.get("duId", ""),
            "sc": a.get("sc", ""),
        }
        if extra:
            q.update(extra)
        return q

    def _app_headers(self) -> dict:
        a = self.auth
        h = dict(APP_HEADERS)
        h["timestamp"] = a.get("ts", str(int(time.time() * 1000)))
        h["qimei36"] = a.get("qimei36", a.get("ostar36", ""))
        if a.get("nonce"):
            h["nonce"] = a["nonce"]
        else:
            h.pop("nonce", None)
        h["model"] = a.get("model", "V2284A")
        h["shield_version"] = a.get("shield_version", "1_20250708")
        for key in ("shield_token", "Host", "Content-Type"):
            if a.get(key):
                h[key] = a[key]
        return h

    def _app_get(self, path: str, params: dict | None = None) -> dict:
        qs = urllib.parse.urlencode(self._app_query(params))
        url = f"{self._app_base()}{path}?{qs}"
        try:
            resp = self.session.get(url, headers=self._app_headers(), timeout=(10, 35))
            resp.raise_for_status()
        except requests.HTTPError:
            log.error("App GET 失败 [%s] %s", resp.status_code, path)
            raise
        data = resp.json()
        if data.get("apiStatus") not in (0, None):
            log.warning("App GET apiStatus=%s msg=%s path=%s",
                        data.get("apiStatus"), data.get("msg"), path)
        return data

    def _app_post(self, path: str, body: dict) -> dict:
        qs = urllib.parse.urlencode(self._app_query())
        h = self._app_headers()
        h["Content-Type"] = "application/json;charset=utf-8"
        url = f"{self._app_base()}{path}?{qs}"
        try:
            resp = self.session.post(url, json=body, headers=h, timeout=(10, 35))
            resp.raise_for_status()
        except requests.HTTPError:
            log.error("App POST 失败 [%s] %s", resp.status_code, path)
            raise
        data = resp.json()
        if data.get("apiStatus") not in (0, None):
            log.warning("App POST apiStatus=%s msg=%s path=%s",
                        data.get("apiStatus"), data.get("msg"), path)
        return data

    # ================================================================ #
    #  搜索
    # ================================================================ #
    def search(self, keyword: str, page_size: int = 40) -> dict:
        """搜索关键字，返回专辑(bookResult) + 主播(announcerResult)。"""
        return self._web_get("/ajax/search", {
            "pageSize": page_size,
            "pageNum": 1,
            "searchOption": "1,2,4",
            "keyWord": keyword,
        })

    # ================================================================ #
    #  专辑 / 主播详情（Web 端）
    # ================================================================ #
    def album_detail(self, book_id: int | str) -> dict:
        """专辑详情（名称、作者、简介、封面等）。"""
        return self._web_get("/ajax/getBookDetail", {"bookId": book_id})

    def album_menu(self, book_id: int | str, page: int = 1,
                   page_size: int = 60, sort_type: int = 0) -> dict:
        """
        专辑目录/音频列表（Web 端，无需登录）。
        每页 60 条，通过 pageNum 翻页获取全部。
        返回的 list 中：id=resId、section=集数、name=标题、tmeId=trackId。
        """
        return self._web_get("/ajax/getBookMenu", {
            "pageNum": page,
            "pageSize": page_size,
            "sortType": sort_type,
            "bookId": book_id,
        })

    def album_audios(self, album_id: int | str, sort_type: int = 0) -> dict:
        """专辑音频列表（联播/精选专辑用）。"""
        return self._web_get("/ajax/getAlbumAudios", {
            "ablumnId": album_id,
            "sortType": sort_type,
        })

    def albums_by_user(self, user_id: int | str, size: int = 20) -> dict:
        """主播（用户）的专辑列表。"""
        return self._web_get("/ajax/getAlbumsByUser", {
            "referId": 0,
            "size": size,
            "userId": user_id,
        })

    # ================================================================ #
    #  播放 / 下载地址
    # ================================================================ #
    def get_listen_path(self, section: int | str, entity_id: int | str,
                        entity_type: int = 1, quality: int = 1) -> str:
        """
        获取单集播放/下载地址（Web 端接口，需要登录 Cookie）。

        Args:
            section:     音频 id（trackId）
            entity_id:   专辑 id（bookId / albumId）
            entity_type: 1=专辑(zhuanji)  2=主播专辑(zhubo)
        """
        if not str(section).isdigit() or int(section) <= 0:
            raise LRTSAPIError("音频 ID 为空或无效，请重新加载专辑")
        if not str(entity_id).isdigit() or int(entity_id) <= 0:
            raise LRTSAPIError("专辑 ID 为空或无效，请重新加载专辑")
        log.info("获取 Web 播放地址：mode=%s entityId=%s section=%s entityType=%s quality=%s",
                 self.mode, entity_id, section, entity_type, quality)
        data = self._web_get("/ajax/getListenPath", {
            "type": 0,
            "section": section,
            "opType": 1,
            "entityType": entity_type,
            "sections": f"[{section}]",
            "entityId": entity_id,
            "quality": max(1, min(int(quality), 3)),
        })
        if data.get("status") == 200 and data.get("data"):
            return data["data"]["path"]
        status = data.get("status")
        msg = data.get("msg") or "获取播放地址失败"
        if status in (1, 5) and msg == "参数错误":
            msg = "Web 登录会话无效或已过期，请重新登录并应用 Cookie"
        log.warning("Web 播放地址被拒绝：status=%s msg=%s entityId=%s section=%s",
                    status, data.get("msg"), entity_id, section)
        raise LRTSAPIError(msg)

    # ---------------------------------------------------------------- #
    #  App 端批量接口（逆向自 gzapi.mting.info）
    # ---------------------------------------------------------------- #
    def app_chapter_list(self, book_id: int | str, page: int = 1,
                         page_size: int = 50) -> dict:
        """App 端章节列表（ClientGetBookResource.action）。"""
        return self._app_get("/bookclient/ClientGetBookResource.action", {
            "bookId": str(book_id), "isUp": "0", "pageNum": str(page),
            "pageSize": str(page_size), "sortType": "0",
        })

    def app_quality_list(self, entity_id: int | str, entity_type: int = 1,
                         res_id: int | str = "", track_id: int | str = "") -> dict:
        """App 端音质列表（getResQualityEffectList）。"""
        return self._app_get("/book/getResQualityEffectList", {
            "entityId": str(entity_id), "entityType": str(entity_type),
            "resId": str(res_id), "trackId": str(track_id),
        })

    def app_get_listen_path(self, entity_id: int | str, res_id: int | str,
                            track_id: int | str, section: int | str,
                            quality: int = 1) -> dict:
        """App 端单集播放地址（getListenPath）。"""
        return self._app_get("/v3/gateway/getListenPath", {
            "costInfo": "1791343473156-1791343475178-0",
            "effect": "0",
            "entityId": str(entity_id),
            "entityType": "1",
            "opType": "0",
            "quality": str(quality),
            "resId": str(res_id),
            "section": str(section),
            "trackId": str(track_id),
            "vid": "",
        })

    def app_batch_listen_path(self, entity_id: int | str,
                              sections: list[dict], quality: int = 1,
                              scene: int = 1) -> list[dict]:
        """
        App 端批量获取播放地址（batchGetListenPath，POST）。

        Args:
            entity_id: 专辑 id
            sections:  [{section, resId, trackId}, ...] 每批建议 ≤10 条
            quality:   1=标准 2=高清 3=极高
        Returns:
            [{"section", "resId", "path", "ekey", "fileSize",
              "md5Code", "bitrate", "quality"}, ...]
        """
        pending = list(sections)
        resolved: dict[str, dict] = {}
        last_error = None
        for requested_quality in range(max(1, min(int(quality), 3)), 0, -1):
            if not pending:
                break
            sections_str = ",".join(f"{s['section']}_{s['resId']}" for s in pending)
            track_ids = ",".join(str(s["trackId"]) for s in pending)
            body = {
                "costInfo": "1791343473156-1791343475178-0",
                "effect": 0,
                "entityId": int(entity_id),
                "entityType": 1,
                "opType": 0,
                "quality": requested_quality,
                "scene": scene,
                "sections": sections_str,
                "trackIds": track_ids,
                "vid": "",
            }
            try:
                resp = self._app_post("/v3/gateway/batchGetListenPath", body)
                if resp.get("apiStatus") != 0:
                    raise LRTSAPIError(
                        f"batchGetListenPath status={resp.get('apiStatus')} "
                        f"msg={resp.get('msg')}"
                    )
            except Exception as e:
                last_error = e
                continue

            for item in (resp.get("data") or {}).get("pathList", []):
                path = item.get("path", "")
                if path:
                    key = str(item.get("section"))
                    resolved[key] = {
                        "section": item.get("section"),
                        "resId": str(item.get("resId", "")),
                        "path": path,
                        "ekey": item.get("ekey", ""),
                        "fileSize": item.get("fileSize", 0),
                        "md5Code": item.get("md5Code", ""),
                        "bitrate": item.get("bitrate", ""),
                        "quality": item.get("quality", requested_quality),
                    }
            pending = [s for s in pending if str(s["section"]) not in resolved]

        if pending and not resolved and last_error:
            raise last_error
        return [resolved[str(s["section"])] for s in sections if str(s["section"]) in resolved]

    # ================================================================ #
    #  用户 / 登录
    # ================================================================ #
    def get_user_info(self) -> dict:
        """当前登录用户信息（用于校验会话是否有效）。"""
        return self._web_get("/ajax/getUserInfo")

    def login_page_url(self) -> str:
        """Web 端登录页地址。"""
        return "https://m.lrts.me/login?redirectUrl=%2Fuser"

    def set_cookie(self, cookie: str) -> None:
        """更新登录会话（Web/小程序模式）。"""
        text = (cookie or "").strip()
        if text.lower().startswith("cookie:"):
            text = text[7:].strip()
        self.session.headers["Cookie"] = text

    def set_auth(self, auth: dict) -> None:
        """更新 App 端签名参数。"""
        self.auth = auth or {}

    @property
    def cookies(self) -> str:
        """当前会话 Cookie（用于持久化）。"""
        header_cookie = self.session.headers.get("Cookie", "")
        if header_cookie:
            return header_cookie
        return "; ".join(f"{k}={v}" for k, v in self.session.cookies.items())


class LRTSAPIError(Exception):
    """懒人听书接口错误。"""
