# -*- coding: utf-8 -*-
"""老师端的门：设备记忆 + 安全头

思路：
- 长链接（带 key）进来一次，这台设备就记住，两年不用再输
- cookie 只存一个由 key 派生的签名，不存 key 本身
- 之后打开 /xin/b 直接进值班室
"""
import hashlib
import hmac

import core

COOKIE = "xok"
TTL = 2 * 365 * 86400          # 两年
FLAG = "xok|v1"


def sig():
    s = (core.get("ops_key") or "") + "|" + FLAG
    return hashlib.sha256(s.encode()).hexdigest()[:32]


def good(v):
    try:
        return bool(v) and hmac.compare_digest(str(v), sig())
    except Exception:
        return False


def remember(resp):
    """给这台设备发一张长期的票"""
    resp.set_cookie(COOKIE, sig(), max_age=TTL, httponly=True,
                    samesite="lax", secure=True, path="/xin")
    return resp


SEC_HEADERS = {
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "SAMEORIGIN",
    "X-Content-Type-Options": "nosniff",
    "X-Robots-Tag": "noindex, nofollow",
}
