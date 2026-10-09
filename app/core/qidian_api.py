# -*- coding: utf-8 -*-
"""
起点听书客户端
===============
基于归档 exe（起点畅听大师）提取的 API 实现：
  - search: qdcg.qidian.com/api/search/list
  - book_detail: qdcg.qidian.com/api/audio/detail
  - chapter_list: qdcg.qidian.com/api/audio/chapter-list
  - play_url: qdcg.qidian.com/api/audio/play
  - 登录: my.qidian.com/?ticket= (扫码后 CDP 抓 Cookie)
"""

from __future__ import annotations

import requests

QDCG_BASE = "https://qdcg.qidian.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Host": "qdcg.qidian.com",
    "Referer": "https://my.qidian.com/",
}


class QidianClient:
    def __init__(self, cookie: str = ""):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.set_cookie(cookie)

    def set_cookie(self, cookie: str) -> None:
        self.session.headers.pop("Cookie", None)
        if cookie:
            self.session.headers["Cookie"] = cookie

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = self.session.get(QDCG_BASE + path, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    def search(self, keyword: str, page: int = 1, page_size: int = 50) -> list:
        """搜索书籍。site=3 表示听书。"""
        data = self._get("/api/search/list", {
            "pageIndex": page,
            "pageSize": page_size,
            "site": 3,
            "model": 1,
            "key": keyword,
        })
        return (data.get("list") or data.get("items") or data.get("data") or [])

    def book_detail(self, adid: str) -> dict:
        """书籍详情。"""
        data = self._get("/api/audio/detail", {"adid": adid})
        return data.get("data") or data

    def chapter_list(self, adid: str, page: int = 1) -> list:
        """章节列表。"""
        data = self._get("/api/audio/chapter-list", {"page": page, "adid": adid})
        items = data.get("Items") or data.get("items") or data.get("list") or []
        return items

    def play_url(self, adid: str, acid: str) -> str:
        """获取章节播放地址。"""
        data = self._get("/api/audio/play", {"adid": adid, "acid": acid})
        # 播放接口返回可能是 url 或 mp3 直链
        if isinstance(data, dict):
            return data.get("url") or data.get("playUrl") or data.get("audioUrl") or ""
        return str(data)

    def login_url(self) -> str:
        return "https://my.qidian.com/?ticket="