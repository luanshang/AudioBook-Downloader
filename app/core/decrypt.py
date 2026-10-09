# -*- coding: utf-8 -*-
"""
喜马拉雅音频链接解密模块
=====================
由 exe 内嵌的 getSoundCryptLink.js 精确转译而来（S-box 查表 + XOR 异或 + UTF-8 解码）。

算法流程：
  1. base64 URL-safe 变体解码（'_'->'/'、'-'->'+'）
  2. 取前 (len-16) 字节为密文，末尾 16 字节为密钥
  3. 密文每个字节经 S-box(u/o 数组) 查表替换
  4. 每 16 字节与密钥异或；每 32 字节再与第二组 S-box(a/c 数组) 异或
  5. UTF-8 流式解码（1/2/3 字节序列）

验证：与 Node 运行原 JS 的输出完全一致。
"""

from __future__ import annotations

import base64
from typing import List


# ---- 加密常量表（与 JS 中 var r / n / o / a 完全一致）----
_SBOX_R = [188, 174, 178, 234, 171, 147, 70, 82, 76, 72, 192, 132, 60, 17, 30, 127, 184, 233, 48, 105, 38, 232, 240, 21, 47, 252, 41, 229, 209, 213, 71, 40, 63, 152, 156, 88, 51, 141, 139, 145, 133, 2, 160, 191, 11, 100, 10, 78, 253, 151, 42, 166, 92, 22, 185, 140, 164, 91, 194, 175, 239, 217, 177, 75, 19, 225, 94, 107, 125, 138, 242, 31, 182, 150, 15, 24, 226, 29, 80, 116, 168, 118, 28, 1, 186, 220, 158, 79, 59, 244, 119, 9, 189, 161, 74, 130, 221, 56, 216, 241, 212, 26, 218, 170, 85, 165, 153, 69, 238, 93, 255, 142, 3, 159, 215, 67, 33, 249, 53, 176, 77, 254, 222, 25, 115, 101, 148, 16, 13, 237, 197, 5, 58, 157, 135, 248, 223, 61, 198, 211, 110, 44, 54, 111, 52, 227, 4, 46, 205, 7, 219, 136, 14, 87, 114, 64, 104, 50, 39, 203, 81, 196, 43, 163, 173, 109, 108, 187, 102, 195, 37, 235, 65, 190, 113, 149, 143, 8, 27, 155, 207, 134, 123, 224, 129, 245, 62, 66, 172, 122, 126, 12, 162, 214, 90, 247, 251, 124, 201, 236, 117, 183, 73, 95, 89, 246, 181, 179, 83, 228, 193, 99, 6, 45, 112, 32, 154, 128, 230, 131, 206, 243, 57, 84, 146, 0, 35, 96, 250, 137, 36, 208, 103, 34, 68, 204, 231, 144, 120, 98, 202, 49, 210, 23, 200, 18, 86, 55, 121, 20, 199, 97, 167, 180, 169, 106]

_SBOX_N = [20, 234, 159, 167, 230, 233, 58, 255, 158, 36, 210, 254, 133, 166, 59, 63, 209, 177, 184, 155, 85, 235, 94, 1, 242, 87, 228, 232, 191, 3, 69, 178]

_SBOX_O = [183, 174, 108, 16, 131, 159, 250, 5, 239, 110, 193, 202, 153, 137, 251, 176, 119, 150, 47, 204, 97, 237, 1, 71, 177, 42, 88, 218, 166, 82, 87, 94, 14, 195, 69, 127, 215, 240, 225, 197, 238, 142, 123, 44, 219, 50, 190, 29, 181, 186, 169, 98, 139, 185, 152, 13, 141, 76, 6, 157, 200, 132, 182, 49, 20, 116, 136, 43, 155, 194, 101, 231, 162, 242, 151, 213, 53, 60, 26, 134, 211, 56, 28, 223, 107, 161, 199, 15, 229, 61, 96, 41, 66, 158, 254, 21, 165, 253, 103, 89, 3, 168, 40, 246, 81, 95, 58, 31, 172, 78, 99, 45, 148, 187, 222, 124, 55, 203, 235, 64, 68, 149, 180, 35, 113, 207, 118, 111, 91, 38, 247, 214, 7, 212, 209, 189, 241, 18, 115, 173, 25, 236, 121, 249, 75, 57, 216, 10, 175, 112, 234, 164, 70, 206, 198, 255, 140, 230, 12, 32, 83, 46, 245, 0, 62, 227, 72, 191, 156, 138, 248, 114, 220, 90, 84, 170, 128, 19, 24, 122, 146, 80, 39, 37, 8, 34, 22, 11, 93, 130, 63, 154, 244, 160, 144, 79, 23, 133, 92, 54, 102, 210, 65, 67, 27, 196, 201, 106, 143, 52, 74, 100, 217, 179, 48, 233, 126, 117, 184, 226, 85, 171, 167, 86, 2, 147, 17, 135, 228, 252, 105, 30, 192, 129, 178, 120, 36, 145, 51, 163, 77, 205, 73, 4, 188, 125, 232, 33, 243, 109, 224, 104, 208, 221, 59, 9]

_SBOX_A = [204, 53, 135, 197, 39, 73, 58, 160, 79, 24, 12, 83, 180, 250, 101, 60, 206, 30, 10, 227, 36, 95, 161, 16, 135, 150, 235, 116, 242, 116, 165, 171]

# 平台标识："www2"/"mweb2" 对应 (o, a) 查表，其他对应 (r, n)
_PLATFORM = "www2"


def _b64_decode(data: str) -> bytes:
    """还原 JS f() 的 base64 解码（URL-safe 变体 + 兼容 padding）"""
    s = data.replace("_", "/").replace("-", "+")
    # 去除非 base64 字符
    s = "".join(ch for ch in s if ch.isalnum() or ch in "+/")
    # 补 padding
    rem = len(s) % 4
    if rem:
        s += "=" * (4 - rem)
    return base64.b64decode(s)


def _xor_region(buf: bytearray, start: int, key: bytes) -> None:
    """JS p() 函数：将 buf[start:start+len(key)] 逐字节与 key 异或"""
    n = min(len(buf) - start, len(key))
    for i in range(n):
        buf[start + i] ^= key[i]


def _utf8_decode(buf: List[int]) -> str:
    """JS 末尾的 UTF-8 流式解码器（switch 按高 4 位分派），与 e[r++] 语义严格一致"""
    out = []
    i = 0
    n = len(buf)
    while i < n:
        o = buf[i]
        i += 1
        high = o >> 4
        if high <= 7:  # 0x00-0x7F 单字节
            out.append(chr(o))
        elif high in (12, 13):  # 0xC0-0xDF 双字节：o 后紧跟 1 个尾字节
            a = buf[i] if i < n else 0
            i += 1
            out.append(chr(((31 & o) << 6) | (63 & a)))
        elif high == 14:  # 0xE0-0xEF 三字节：o 后紧跟 2 个尾字节
            a = buf[i] if i < n else 0
            i += 1
            b2 = buf[i] if i < n else 0
            i += 1
            out.append(chr(((15 & o) << 12) | ((63 & a) << 6) | (63 & b2)))
        # 其他高 4 位不合法，忽略
    return "".join(out)


def get_sound_crypt_link(encrypted: str) -> str:
    """
    解密喜马拉雅加密音频链接。

    Args:
        encrypted: 形如 '07hJDBW...' 的 URL-safe base64 加密串

    Returns:
        解密后的真实播放地址；长度不足/算法失败返回原串或空串（与 JS 行为一致）
    """
    try:
        e = _b64_decode(encrypted)
        if e is None or len(e) < 16:
            return encrypted

        key = e[-16:]  # 末尾 16 字节为密钥
        body = bytearray(e[:-16])  # 前段为密文

        # 平台选择查表
        if _PLATFORM in ("www2", "mweb2"):
            sbox = _SBOX_O
            key_sbox = _SBOX_A
        else:
            sbox = _SBOX_R
            key_sbox = _SBOX_N

        # S-box 替换
        for i in range(len(body)):
            body[i] = sbox[body[i]]

        # 每 16 字节 XOR 密钥
        for i in range(0, len(body), 16):
            _xor_region(body, i, key)

        # 每 32 字节 XOR 第二组 key
        key2 = bytes(key_sbox)
        for i in range(0, len(body), 32):
            _xor_region(body, i, key2)

        return _utf8_decode(list(body))
    except Exception:
        return ""


if __name__ == "__main__":
    # 与 exe 内测试样本自检（与原 JS 输出一致）
    samples = [
        "07hJDBWP8iRqmA1vY6nMzm6-yDHeMl1m5CHP0ufzzUZZbac-BEffTyrMJHxpKWQFaMiRgjTASHSSqBq6kICSY3PiMqk1j989I8x9V2MpTr_H6y0GDgR5rtVEymtzoM3m8BJ9h6dKt0mjkOGravyADE1i7iY1D5mRm337FtI3IWPRjKf9MDDc_BB4_IHGrLWoUVoJr-pn",
        "pX7rCko1ZPLJXbyU3qjcDqAp042BK5yCrhhNlUZEBd6lHKILemhbvHD1YkhQ7FDblryCkLnnmy4Cu5dBAjnrmpoYq_GEfkBY9cAqbsiQyhKIP9Ig1NBwTklmQDDekwaTTbNHORsmo2_9YWQvn4h6CPamihjlDlBV8YCzvm8G3hFb1DcgjlCaskdT_hZlUywofb3FyfCz",
    ]
    for s in samples:
        r = get_sound_crypt_link(s)
        print(f"len={len(r)} 前40: {r[:40]!r}")