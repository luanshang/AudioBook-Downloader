# -*- coding: utf-8 -*-
"""
喜马拉雅客户端
===============
基于归档 exe（喜马M4A下载器）提取的 API 实现：
  - search: 关键字搜索
  - parse_album: 解析专辑网址/ID -> 曲目列表
  - get_track_url: 获取单曲真实播放地址（含 getSoundCryptLink 解密）
  - 扫码登录：passport.ximalaya.com/web/qrCode/*
"""

from __future__ import annotations

import re
import requests

from app.core.decrypt import get_sound_crypt_link

MOBILE_BASE = "https://mobile.ximalaya.com"
PC_BASE = "https://pc.ximalaya.com"
WWW_BASE = "https://www.ximalaya.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0_1 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
        "MicroMessenger/8.0.53"
    ),
    "Accept": "application/json",
}


class XimalayaClient:
    def __init__(self, cookie: str = ""):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        if cookie:
            self.session.headers["Cookie"] = cookie

    # ------------------------------------------------------------------ #
    # 搜索
    # ------------------------------------------------------------------ #
    def search(self, keyword: str, page: int = 1, page_size: int = 20) -> tuple[list, list]:
        """搜索，返回 (专辑列表, 声音列表)。"""
        try:
            resp = self.session.get(
                f"{WWW_BASE}/revision/search",
                params={"key": keyword, "page": page, "pageSize": page_size},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
                         "Referer": f"{WWW_BASE}/"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            albums = (data.get("album", {}) or {}).get("list", [])
            sounds = (data.get("sound", {}) or {}).get("list", [])
            return albums, sounds
        except Exception:
            return [], []

    # ------------------------------------------------------------------ #
    # 专辑解析
    # ------------------------------------------------------------------ #
    def _album_id_from(self, url_or_id: str) -> str:
        s = url_or_id.strip()
        m = re.search(r"/album/(\d+)", s)
        if m:
            return m.group(1)
        if s.isdigit():
            return s
        raise ValueError("无法识别专辑网址/ID")

    def parse_album(self, url_or_id: str) -> dict:
        """解析专辑，返回 {ok, album, tracks}。"""
        album_id = self._album_id_from(url_or_id)

        # PC 接口获取曲目列表
        headers_pc = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"}
        resp = self.session.get(
            f"{PC_BASE}/simple-revision-for-pc/album/v1/getTracksList",
            params={"albumId": album_id, "pageNum": 1, "pageSize": 30, "sort": 0},
            headers=headers_pc,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("ret") != 0:
            return {"ok": False, "error": data.get("msg", "解析失败")}

        album_info = (data.get("data") or {}).get("album") or {}
        tracks = []
        for t in (data.get("data") or {}).get("tracks") or []:
            tracks.append({
                "id": str(t.get("id")),
                "title": t.get("title", ""),
                "duration": t.get("duration", 0),
                "playCount": t.get("playCount", 0),
            })
        # 翻页获取全部（最多 10 页）
        page = 2
        while len(tracks) < 300 and page <= 10:
            try:
                resp2 = self.session.get(
                    f"{PC_BASE}/simple-revision-for-pc/album/v1/getTracksList",
                    params={"albumId": album_id, "pageNum": page, "pageSize": 30, "sort": 0},
                    headers=headers_pc,
                    timeout=15,
                )
                d2 = resp2.json()
                page_tracks = (d2.get("data") or {}).get("tracks") or []
                if not page_tracks:
                    break
                for t in page_tracks:
                    tracks.append({
                        "id": str(t.get("id")),
                        "title": t.get("title", ""),
                        "duration": t.get("duration", 0),
                        "playCount": t.get("playCount", 0),
                    })
                page += 1
            except Exception:
                break

        return {
            "ok": True,
            "album": {"id": album_id, "title": album_info.get("title", ""),
                      "intro": album_info.get("intro", ""), "cover": album_info.get("cover", "")},
            "tracks": tracks,
        }

    # ------------------------------------------------------------------ #
    # 单曲播放地址（含解密）
    # ------------------------------------------------------------------ #
    def get_track_url(self, track_id: str, quality: int = 1) -> str:
        """获取单曲真实播放地址（playPathList 加密链接解密）。"""
        resp = self.session.get(
            f"{WWW_BASE}/mobile-playpage/track/v3/baseInfo/{track_id}",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
                     "Referer": f"{WWW_BASE}/"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data") or {}

        play_paths = data.get("playPathList") or []
        if not play_paths:
            raise ValueError("未找到播放路径")

        chosen = None
        for p in play_paths:
            if p.get("quality") == quality:
                chosen = p
                break
        if chosen is None:
            chosen = play_paths[0]

        raw_url = chosen.get("url") or ""
        crypt_flag = chosen.get("cryptFlag") or 0

        if raw_url.startswith("http"):
            return raw_url
        if crypt_flag or raw_url:
            dec = get_sound_crypt_link(raw_url)
            if dec:
                return dec
        raise ValueError("音频链接解密失败")

    # ------------------------------------------------------------------ #
    # 扫码登录
    # ------------------------------------------------------------------ #
    def qr_gen(self) -> dict:
        resp = self.session.get(
            "https://passport.ximalaya.com/web/qrCode/gen",
            params={"level": "L", "source": "喜马拉雅电脑版"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def qr_check(self, short_id: str) -> dict:
        resp = self.session.get(
            f"https://passport.ximalaya.com/web/qrCode/check/{short_id}",
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def current_user(self) -> dict:
        resp = self.session.get(f"{WWW_BASE}/revision/main/getCurrentUser", timeout=15)
        resp.raise_for_status()
        return resp.json()