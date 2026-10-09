# -*- coding: utf-8 -*-
"""
从 aardio exe 中提取 API 信息（URL、路径、请求头、加密算法）
"""
import re
import os
import sys


def extract_strings(path: str) -> list[tuple[int, str]]:
    """提取全部可读字符串（含中文），返回 (offset, text) 列表。"""
    data = open(path, "rb").read()
    out = []
    # ASCII 可读
    for m in re.finditer(rb"[\x20-\x7e]{4,}", data):
        s = m.group(0).decode("ascii", "ignore")
        if s.strip():
            out.append((m.start(), s))
    # 中文 UTF-8
    for m in re.finditer(rb"(?:[\xe4-\xe9][\x80-\xbf][\x80-\xbf]){2,}", data):
        try:
            s = m.group(0).decode("utf-8")
            if s.strip():
                out.append((m.start(), s))
        except Exception:
            pass
    out.sort(key=lambda x: x[0])
    return out


def analyze(path: str):
    print("=" * 78)
    print("FILE:", os.path.basename(path))
    print("=" * 78)
    data = open(path, "rb").read()
    print("大小:", len(data), "aardio:", data.find(b"=aardio") >= 0)

    strs = extract_strings(path)
    # 提取 URL / API 路径 / 关键域
    urls = set()
    apis = set()
    for _, s in strs:
        for m in re.finditer(r"https?://[^\s\"'<>]{6,}", s):
            urls.add(m.group(0)[:120])
        for m in re.finditer(r"/api/[A-Za-z0-9/_.-]{4,}", s):
            apis.add(m.group(0)[:120])
        for m in re.finditer(r"/ajax/[A-Za-z0-9/_.-]{4,}", s):
            apis.add(m.group(0)[:120])

    print("\n--- URL 列表 (%d) ---" % len(urls))
    for u in sorted(urls):
        print("  ", u)
    print("\n--- API 路径 (%d) ---" % len(apis))
    for a in sorted(apis):
        print("  ", a)

    # 中文字符串（UI/功能提示）
    cn = [s for _, s in strs if re.match(r"^[\u4e00-\u9fff]", s)]
    print("\n--- 中文字符串 (%d) ---" % len(cn))
    for s in cn[:40]:
        print("  ", s[:80])
    print()


if __name__ == "__main__":
    base = r"E:\AI\Chat\WorkSpace\Software\AudioBook Downloader\_archive"
    for f in ["喜马M4A下载器v1.0.2.exe", "喜马MP3下载器v1.0.0.exe", "起点畅听大师v1.0.1.exe"]:
        analyze(os.path.join(base, f))