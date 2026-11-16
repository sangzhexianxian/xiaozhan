# -*- coding: utf-8 -*-
"""夜话 · 网页通话（TRTC）
挂载：app.py 末尾  import call; call.install(APP)

两条进门口：
  /xin/call/{key}/{bid}?r=boss   老师（ops key 保护）
  /xin/join/{token}              粉丝（预约时发的门牌链接）
"""
import base64
import hashlib
import hmac
import json
import os
import sqlite3
import time

import core
import live

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "call.html")
KEYFILE = os.environ.get("TRTC_KEYFILE", "")


def _c():
    c = sqlite3.connect(core.DB)
    c.row_factory = sqlite3.Row
    return c


def secret():
    try:
        return open(KEYFILE).read().strip()
    except Exception:
        return ""


def appid():
    try:
        return int(core.get("trtc_appid") or 0)
    except Exception:
        return 0


def usersig(uid, expire=86400 * 2):
    """用腾讯官方库签发（实测只有这个格式能进房）"""
    sid = appid()
    k = secret()
    if not sid or not k:
        return ""
    try:
        import TLSSigAPIv2
        return TLSSigAPIv2.TLSSigAPIv2(sid, k).gen_sig(uid, expire)
    except Exception:
        return ""


def _sub(dm):
    if dm <= 0:
        return "到点了，可以接"
    if dm >= 1440:
        return "约在 %d 天后 · 现在也能先试" % (dm // 1440)
    if dm >= 60:
        return "还有 %d 小时 · 现在也能先试" % (dm // 60)
    return "还有 %d 分钟 · 现在也能先试" % dm


def render(row, role, key=""):
    """把一场预约渲染成通话页"""
    t0 = time.mktime(live._dt(row["slot"]))
    dm = int((t0 - time.time()) / 60)
    sid = appid()
    uid = "ysboss" if role == "boss" else ("ysu%d" % row["uid"])
    sig = usersig(uid)
    room = 100000 + int(row["id"]) * 7 + int(time.strftime("%d")) * 13
    back = ("/xin/boss/%s" % key) if (role == "boss" and key) else "/xin/live"

    html = open(PAGE, encoding="utf-8").read()
    rep = {
        "@@AVATAR@@": "/xin/m/avatar-s.png",
        "@@NAME@@": ((row["nick"] or "对方") if role == "boss"
                     else (core.get("brand") or "老师")),
        "@@PEER@@": (row["nick"] or "对方") if role == "boss" else "他",
        "@@KIND@@": live.LABEL.get(row["kind"], ""),
        "@@KINDRAW@@": row["kind"] or "voice",
        "@@SUB@@": _sub(dm),
        "@@BACK@@": back,
        "@@KEY@@": key or "",
        "@@SDKAPPID@@": str(sid),
        "@@USERSIG@@": sig,
        "@@USERID@@": uid,
        "@@ROOMID@@": str(room),
        "@@BID@@": str(row["id"]),
        "@@ROLE@@": role,
    }
    for k, v in rep.items():
        html = html.replace(k, str(v))
    return html


# bid -> {"ts": 拨出时刻, "role": 谁拨的}
CALLING = {}


def install(app):
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    def _ok(key):
        return bool(key) and key == core.get("ops_key")

    def _row_bid(bid):
        c = _c()
        r = c.execute("""SELECT b.*, u.nick FROM booking b LEFT JOIN usr u ON u.id=b.uid
                         WHERE b.id=?""", (bid,)).fetchone()
        c.close()
        return r

    def _row_tok(tok):
        c = _c()
        r = c.execute("""SELECT b.*, u.nick FROM booking b LEFT JOIN usr u ON u.id=b.uid
                         WHERE b.token=?""", (tok,)).fetchone()
        c.close()
        return r

    @app.get("/xin/call/{key}/{bid}", response_class=HTMLResponse)
    def _call(key: str, bid: int, r: str = ""):
        if not _ok(key):
            return HTMLResponse("<h2>没有入口</h2>", status_code=403)
        row = _row_bid(bid)
        if not row:
            return HTMLResponse("<h2>没有这一场</h2>", status_code=404)
        role = "boss" if (r or "").strip().lower() == "boss" else "fan"
        return render(row, role, key)

    @app.get("/xin/join/{token}", response_class=HTMLResponse)
    def _join(token: str):
        row = _row_tok((token or "").strip())
        if not row:
            return HTMLResponse(
                "<div style='background:#0a0a0a;color:#ddd6c8;font-family:-apple-system,sans-serif;"
                "padding:60px 24px;text-align:center;min-height:100vh;line-height:2'>"
                "<div style='font-size:17px'>这个门牌不在了</div>"
                "<div style='font-size:13px;color:#7d766a;margin-top:12px'>"
                "可能已经被取消，或者链接抄漏了几位<br>"
                "<a href='/xin/live' style='color:#c9a961'>回预约页重新约一场</a></div></div>",
                status_code=404)
        return render(row, "fan")

    @app.post("/xin/api/call/end")
    async def _end(req: Request):
        d = await req.json()
        bid = int(d.get("id") or 0)
        secs = int(d.get("secs") or 0)
        key = d.get("key") or ""
        if key and not _ok(key):
            return {"ok": 0, "msg": "没有权限"}
        if secs <= 0:
            return {"ok": 0}
        c = _c()
        r = c.execute("SELECT * FROM booking WHERE id=?", (bid,)).fetchone()
        if not r:
            c.close()
            return {"ok": 0}
        if r["secs"] and r["secs"] >= secs:
            c.close()
            return {"ok": 1, "secs": r["secs"]}
        c.execute("UPDATE booking SET start_at=COALESCE(NULLIF(start_at,''),?), end_at=?, secs=?,"
                  " status='done', done_at=? WHERE id=?",
                  (core.now(), core.now(), secs, core.now(), bid))
        c.commit()
        c.close()
        CALLING.pop(bid, None)
        return {"ok": 1, "secs": secs}

    @app.post("/xin/api/call/ping")
    async def _ping(req: Request):
        d = await req.json()
        bid = int(d.get("id") or 0)
        role = (d.get("role") or "fan").strip().lower()
        if bid <= 0:
            return {"ok": 0}
        if role not in ("boss", "fan"):
            role = "fan"
        CALLING[bid] = {"ts": time.time(), "role": role}
        return {"ok": 1}

    @app.get("/xin/api/call/waiting")
    def _waiting(bid: int = 0):
        v = CALLING.get(bid)
        if not v:
            return {"calling": 0}
        age = int(time.time() - v["ts"])
        if age > 180:
            CALLING.pop(bid, None)
            return {"calling": 0}
        return {"calling": 1, "by": v["role"], "age": age}

    @app.post("/xin/api/call/stop")
    async def _stop(req: Request):
        d = await req.json()
        CALLING.pop(int(d.get("id") or 0), None)
        return {"ok": 1}

    @app.get("/xin/api/call/state")
    def _state():
        return {"appid": appid(), "hasKey": bool(secret())}

    @app.post("/xin/api/call/setappid")
    async def _setappid(req: Request):
        d = await req.json()
        if not _ok(d.get("key") or ""):
            return {"ok": 0, "msg": "没有权限"}
        v = str(d.get("appid") or "").strip()
        if not v.isdigit():
            return {"ok": 0, "msg": "SDKAppID 是纯数字"}
        core.set("trtc_appid", v)
        return {"ok": 1, "appid": int(v)}
