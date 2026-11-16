# -*- coding: utf-8 -*-
"""小站的信 · Web 服务（端口 8872）"""
import os
import re
import shutil
import time

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import (FileResponse, HTMLResponse, JSONResponse,
                               RedirectResponse)

import core
import ui
import conf

APP = FastAPI(title="小站的信")
KEY = core.init()


def _cfg():
    return {
        "CSS": ui.XIN_CSS,
        "BRAND": core.get("brand"),
        "MARK": core.get("brand")[:1] or "山",
        "SUB1": "有些话，说不出口的，",
        "SUB2": "写在这里。",
        "SUB3": "只有我看到",
        "P_REPLY": core.get("price_reply"),
        "P_R1": core.get("price_r1"),
        "P_R2": core.get("price_r2"),
        "P_R3": core.get("price_r3"),
        "FOOT": "我 会 亲 自 看",
    }


# ---------------------------------------------------------------- 安全门
try:
    import guard as _g

    @APP.middleware("http")
    async def _sec_mw(request, call_next):
        resp = await call_next(request)
        try:
            p = request.url.path
            if p.startswith(("/xin/boss/", "/xin/setup/", "/xin/pay/", "/xin/orders/",
                             "/xin/liveops/", "/xin/chatlog/", "/xin/d/")):
                seg = p.rstrip("/").split("/")[-1]
                if seg and seg in ((core.get("ops_key") or ""), (core.get("desk_key") or "")):
                    _g.remember(resp)
        except Exception:
            pass
        for _k, _v in _g.SEC_HEADERS.items():
            resp.headers[_k] = _v
        return resp

    @APP.get("/xin/b", response_class=HTMLResponse)
    def _short_entry(request: Request):
        """老师收藏这一个短地址：记住过就直接进，否则告诉他用长链接"""
        from fastapi.responses import RedirectResponse as _RR
        if _g.good(request.cookies.get(_g.COOKIE)):
            return _RR("/xin/boss/" + (core.get("ops_key") or ""), status_code=302)
        return HTMLResponse("""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>值班室</title><style>
body{background:#171310;color:#E8DFCF;font-family:-apple-system,"PingFang SC",sans-serif;
 min-height:100vh;display:flex;align-items:center;justify-content:center;padding:26px}
.b{width:100%;max-width:340px;text-align:center}
h1{font-family:"Songti SC",serif;font-size:22px;letter-spacing:.3em;color:#F0E4CB;margin-bottom:8px}
p{font-size:14px;color:#A79C89;line-height:2.1;margin-bottom:20px}
.k{background:rgba(201,169,97,.07);border:1px solid rgba(201,169,97,.16);
 border-radius:12px;padding:17px;font-size:13px;color:#8C8170;line-height:2.1;text-align:left}
.k b{color:#C9A961;font-weight:500}
</style></head><body><div class="b">
<h1>值 班 室</h1>
<p>这台设备还没被记住</p>
<div class="k">
如果是<b>你自己</b>换了手机、清了浏览器，<br>
用微信收藏里那条<b>长链接</b>打开一次就行，<br>
以后点短地址就能进。<br><br>
真找不到了，问一声，<br>请人给你<b>换一条新的</b>。
</div>
<div style="margin-top:26px"><a href="/xin/" style="color:#8C8170;
 font-size:14px;text-decoration:none;border-bottom:1px solid rgba(201,169,97,.3);
 padding-bottom:3px">我不是他，我要看门厅 ›</a></div>
</div></body></html>""", headers=dict(_g.SEC_HEADERS))

except Exception as _e:
    print("[guard] init failed:", _e)


# ---------------------------------------------------------------- 收件页
@APP.get("/xin")
def xin_redirect():
    return RedirectResponse("/xin/", status_code=301)


@APP.get("/xin/liuyan", response_class=HTMLResponse)
def xin_index():
    if core.get("paused") == "1":
        return HTMLResponse(
            "<!DOCTYPE html><html><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<style>body{background:#0a0d0c;color:#918d85;font-family:sans-serif;"
            "display:flex;align-items:center;justify-content:center;height:100vh;margin:0;"
            "text-align:center;line-height:2;font-size:15px}</style></head><body>"
            "<div>这周排满了<br><span style='font-size:13px'>下周再来</span></div>"
            "</body></html>",
            headers={"Cache-Control": "no-store"},
        )
    return HTMLResponse(ui.xin_page(_cfg()), headers={"Cache-Control": "no-store"})


@APP.post("/xin/api/voice")
def xin_voice(f: UploadFile = File(...)):
    ts = int(time.time() * 1000)
    raw = os.path.join(core.MEDIA, "in_%d.raw" % ts)
    with open(raw, "wb") as fp:
        shutil.copyfileobj(f.file, fp)
    dst = os.path.join(core.MEDIA, "in_%d.mp3" % ts)
    ok, err = core.to_mp3(raw, dst)
    try:
        os.remove(raw)
    except Exception:
        pass
    if not ok:
        return {"ok": 0, "msg": "录音没处理好，再录一次"}
    return {"ok": 1, "file": os.path.basename(dst), "url": "/xin/m/" + os.path.basename(dst)}


@APP.post("/xin/api/in")
async def xin_in(req: Request):
    d = await req.json()
    kind = d.get("kind")
    if kind not in ("reply", "read"):
        return {"ok": 0, "msg": "先选一项"}
    note = (d.get("note") or "").strip()
    audio = (d.get("audio") or "").strip()
    if not note and not audio:
        return {"ok": 0, "msg": "还没写呢"}
    # 价格
    tier = d.get("tier") or "r2"
    if kind == "reply":
        price = int(core.get("price_reply", "99") or 99)
        tier = ""
    else:
        pm = {"r1": "price_r1", "r2": "price_r2", "r3": "price_r3"}
        price = int(core.get(pm.get(tier, "price_r2"), "69") or 69)
    reqs = []
    if d.get("tone"):
        reqs.append("语气：" + d["tone"])
    if d.get("use"):
        reqs.append("用途：" + d["use"])
    tok = core.new_token(10)
    tid = core.ex(
        "INSERT INTO threads(kind,price,status,nick,contact,note,req,tier,audio_in,created,token)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (kind, price, "pending", (d.get("nick") or "").strip()[:20],
         (d.get("contact") or "").strip()[:40], note, "；".join(reqs), tier, audio,
         core.now(), tok),
    )
    hit = core.crisis_hit(note)
    warn = ""
    try:
        import words as _w
        warn = _w.brief(note)
    except Exception:
        pass
    return {"ok": 1, "id": tid, "tok": tok, "crisis": 1 if hit else 0,
            "warn": warn, "price": price}


@APP.post("/xin/api/thread/claim")
async def thread_claim(req: Request):
    """粉丝点了「我已经付好了」——通知他，但不等于入账"""
    d = await req.json()
    tok = (d.get("tok") or "").strip()
    if not tok:
        return {"ok": 0, "msg": "没有单号"}
    r = core.one("SELECT * FROM threads WHERE token=?", (tok,))
    if not r:
        return {"ok": 0, "msg": "没这单"}
    if r["status"] in ("paid", "done"):
        return {"ok": 1, "already": 1}
    core.ex("UPDATE threads SET status='claimed', paid_at=? WHERE id=?", (core.now(), r["id"]))
    try:
        import subprocess
        key = core.get("ops_key")
        n = (r["note"] or "")[:120].replace("<", "&lt;")
        hp = "/tmp/xin_claim_%d.html" % r["id"]
        with open(hp, "w", encoding="utf-8") as f:
            f.write('<div style="font-family:-apple-system,sans-serif;padding:10px;'
                    'font-size:15px;line-height:1.9">'
                    '<h2 style="font-size:17px">有人付了钱，等你确认</h2>'
                    '<p>%s　￥%d　（%s）</p>'
                    '<p style="background:#f6f2ea;padding:12px;border-radius:8px;'
                    'color:#333;font-size:14px">%s</p>'
                    '<p style="font-size:13px;color:#666">他没真转账你也没法知道，'
                    '看一眼微信有没有这笔，收下再点确认。</p>'
                    '<p><a href="' + conf.u("/xin/d/%s") + '">去确认 ›</a></p>'
                    '</div>' % ((r["nick"] or "有人"), r["price"],
                                core.now()[:16], n or "（语音留言）", key))
        subprocess.run([conf.PYBIN, conf.SENDMAIL,
                        "--to", conf.OPS_EMAIL, "--from-name", conf.MAIL_FROM,
                        "--subject", "有人付了 %d 元，等你确认" % r["price"],
                        "--html", hp],
                       stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
    except Exception as _e:
        print("[claim mail]", _e)
    return {"ok": 1}


@APP.get("/xin/m/{name}")
def media(name: str):
    p = os.path.join(core.MEDIA, os.path.basename(name))
    if not os.path.exists(p):
        return JSONResponse({"ok": 0}, status_code=404)
    low = name.lower()
    if low.endswith(".png"):
        mt = "image/png"
    elif low.endswith((".jpg", ".jpeg")):
        mt = "image/jpeg"
    else:
        mt = "audio/mpeg"
    return FileResponse(p, media_type=mt)


@APP.post("/xin/api/pay")
def api_pay(f: UploadFile = File(...), key: str = Form("")):
    if not key or key != core.get("ops_key"):
        return {"ok": 0, "msg": "链接不对"}
    raw = os.path.join(core.MEDIA, "_pay.raw")
    with open(raw, "wb") as fp:
        shutil.copyfileobj(f.file, fp)
    try:
        from PIL import Image
        im = Image.open(raw).convert("RGB")
        w, h = im.size
        s0 = min(w, h)
        im = im.crop(((w - s0) // 2, (h - s0) // 2, (w + s0) // 2, (h + s0) // 2))
        im.resize((720, 720), Image.LANCZOS).save(os.path.join(core.MEDIA, "pay.png"))
    except Exception as e:
        return {"ok": 0, "msg": "图片读不了：%s" % str(e)[:40]}
    try:
        os.remove(raw)
    except Exception:
        pass
    return {"ok": 1, "v": int(time.time())}


# ---------------------------------------------------------------- 工作台
def _auth(key):
    return key and key == core.get("desk_key")


@APP.get("/xin/d")
def desk_root():
    return HTMLResponse("<h2 style='font-family:sans-serif'>链接不完整</h2>", status_code=404)


@APP.get("/xin/d/{key}", response_class=HTMLResponse)
def desk_list(key: str):
    if not _auth(key):
        return HTMLResponse("<h2 style='font-family:sans-serif'>链接不对</h2>", status_code=403)
    todo = core.q("SELECT * FROM threads WHERE status IN ('pending','claimed')"
                  " ORDER BY id DESC")
    done = core.q("SELECT * FROM threads WHERE status IN ('paid','done') ORDER BY id DESC LIMIT 30")
    m = time.strftime("%Y-%m")
    rows = core.q("SELECT kind,price FROM threads WHERE status IN ('paid','done') AND created LIKE ?", (m + "%",))
    total = sum(r["price"] for r in rows)
    stat = "%d 单" % len(rows)
    m_cnt = len(rows)
    m_fee = int(round(total * 0.1))
    m_reply = sum(1 for r in rows if r["kind"] == "reply")
    m_break = "回信 %d 单 · 代读 %d 单" % (m_reply, m_cnt - m_reply)

    def item(r):
        kind = "回 信" if r["kind"] == "reply" else "代 读"
        meta = []
        if r["nick"]:
            meta.append(r["nick"])
        if r["tier"]:
            meta.append({"r1": "100字内", "r2": "300字内", "r3": "600字内"}.get(r["tier"], ""))
        if r["status"] == "claimed":
            meta.insert(0, "⚠ 他说付了 · 等你确认")
        try:
            import words as _w
            _b = _w.brief(r["note"] or "")
            if _b:
                meta.append("⚠ " + _b)
        except Exception:
            pass
        snip = (r["note"] or "[ 只有语音 ]").replace("\n", " ")[:40]
        return (ui.DESK_ITEM
                .replace("@@URL@@", "/xin/d/%s/t/%d" % (key, r["id"]))
                .replace("@@CLS@@", "todo" if r["status"] == "pending" else "")
                .replace("@@KIND@@", kind)
                .replace("@@META@@", " · ".join([x for x in meta if x]))
                .replace("@@SNIP@@", snip)
                .replace("@@PRICE@@", "￥%d" % r["price"])
                .replace("@@AGE@@", _age(r["created"])))

    todo_html = "".join(item(r) for r in todo) or ui.DESK_EMPTY
    done_html = "".join(item(r) for r in done) or '<div class="empty">还没有交付过</div>'
    html = (ui.DESK_LIST
            .replace("@@HEAD@@", ui.desk_head(stat, "工作台", "本月"))
            .replace("@@N1@@", str(len(todo)))
            .replace("@@N2@@", str(len(done)))
            .replace("@@TODO@@", todo_html)
            .replace("@@DONE@@", done_html)
            .replace("@@M_CNT@@", str(m_cnt))
            .replace("@@M_TOTAL@@", str(total))
            .replace("@@M_FEE@@", str(m_fee))
            .replace("@@M_NET@@", str(total - m_fee))
            .replace("@@M_BREAK@@", m_break))
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


def _age(t):
    try:
        ts = time.mktime(time.strptime(t, "%Y-%m-%d %H:%M:%S"))
    except Exception:
        return ""
    tm = time.localtime(ts)
    if time.strftime("%Y-%m-%d", tm) == time.strftime("%Y-%m-%d"):
        return "今天 " + time.strftime("%H:%M", tm)
    return time.strftime("%m-%d %H:%M", tm)


@APP.get("/xin/d/{key}/t/{tid}", response_class=HTMLResponse)
def desk_detail(key: str, tid: int):
    if not _auth(key):
        return HTMLResponse("<h2 style='font-family:sans-serif'>链接不对</h2>", status_code=403)
    r = core.one("SELECT * FROM threads WHERE id=?", (tid,))
    if not r:
        return HTMLResponse("<h2>没有这一单</h2>", status_code=404)
    draft = r["final_text"] or r["draft"] or ""
    segs = _split_text(draft) if draft else []
    if segs:
        seg_head = "二 · 念 · 共 %d 段" % len(segs)
        segs_html = "".join(ui.seg_html(i, s) for i, s in enumerate(segs))
    else:
        seg_head = "二 · 念"
        segs_html = ('<div style="font-size:15.5px;color:#6E665C;line-height:1.9;'
                     'padding:6px 0 14px">先把上面写好。<br>写好了，这里会自动分成几段，'
                     '你一段一段念。</div>')
    audio_html = ""
    if r["audio_in"]:
        audio_html = '<audio controls src="/xin/m/%s"></audio>' % r["audio_in"]
    meta2 = " · ".join([x for x in [r["nick"], r["contact"], r["req"], _age(r["created"])] if x])
    html = (ui.DESK_DETAIL
            .replace("@@HEAD@@", ui.desk_head("￥%d" % r["price"], "处理一单",
                                            "回信" if r["kind"] == "reply" else "代读"))
            .replace("@@BACK@@", "/xin/d/" + key)
            .replace("@@NOTE@@", _esc(r["note"] or "[ 客户只留了语音 ]"))
            .replace("@@AUDIO@@", audio_html)
            .replace("@@META2@@", _esc(meta2))
            .replace("@@DRAFT@@", _esc(draft))
            .replace("@@SEGHEAD@@", seg_head)
            .replace("@@NSEG@@", str(len(segs)))
            .replace("@@SEGS@@", segs_html)
            .replace("@@TID@@", str(tid))
            .replace("@@OUT@@", r["audio_out"] or "")
            .replace("@@TOKEN@@", r["token"] or "")
            .replace("@@API@@", "/xin/api")
            .replace("@@SEND_DIS@@", "" if r["audio_out"] else "style='opacity:.42'"))
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))





# ---------------------------------------------------------------- 工作台 API
@APP.post("/xin/api/gen")
async def api_gen(req: Request):
    d = await req.json()
    r = core.one("SELECT * FROM threads WHERE id=?", (int(d.get("id", 0)),))
    if not r:
        return {"ok": 0, "msg": "没有这一单"}
    try:
        txt = core.draft_reply(r["note"] or "", r["req"] or "")
    except Exception as e:
        return {"ok": 0, "msg": "模型没应答：%s" % str(e)[:60]}
    core.ex("UPDATE threads SET draft=? WHERE id=?", (txt, r["id"]))
    return {"ok": 1, "text": txt}


@APP.post("/xin/api/polish")
async def api_polish(req: Request):
    d = await req.json()
    txt = (d.get("text") or "").strip()
    if len(txt) < 50:
        return {"ok": 0, "msg": "稿子太短"}
    try:
        out = core.polish(txt, d.get("instr") or "润色一下")
    except Exception as e:
        return {"ok": 0, "msg": "模型没应答：%s" % str(e)[:60]}
    core.ex("UPDATE threads SET draft=? WHERE id=?", (out, int(d.get("id", 0))))
    return {"ok": 1, "text": out}


@APP.post("/xin/api/split")
async def api_split(req: Request):
    d = await req.json()
    tid = int(d.get("id", 0))
    txt = (d.get("text") or "").strip()
    core.ex("UPDATE threads SET final_text=? WHERE id=?", (txt, tid))
    segs = _split_text(txt)
    html = "".join(ui.seg_html(i, s) for i, s in enumerate(segs))
    return {"ok": 1, "n": len(segs), "html": html}


@APP.post("/xin/api/seg")
def api_voice(f: UploadFile = File(...), id: str = Form(...), seg: str = Form("1"),
              seq: str = Form("0")):
    tid = int(id)
    ts = int(time.time() * 1000)
    raw = os.path.join(core.MEDIA, "t%d_s%s_%d.raw" % (tid, seg, ts))
    with open(raw, "wb") as fp:
        shutil.copyfileobj(f.file, fp)
    dst = os.path.join(core.MEDIA, "t%d_s%03d.mp3" % (tid, int(seg)))
    ok, err = core.to_mp3(raw, dst)
    try:
        os.remove(raw)
    except Exception:
        pass
    if not ok:
        return {"ok": 0, "msg": "录音格式不对"}
    return {"ok": 1, "seg": seg}


@APP.post("/xin/api/take")
def api_take(f: UploadFile = File(...), id: str = Form(...)):
    """提词器整段录音：一次录完，直接成片"""
    tid = int(id)
    r = core.one("SELECT * FROM threads WHERE id=?", (tid,))
    if not r:
        return {"ok": 0, "msg": "没有这一单"}
    ts = int(time.time() * 1000)
    raw = os.path.join(core.MEDIA, "take_%d_%d.raw" % (tid, ts))
    with open(raw, "wb") as fp:
        shutil.copyfileobj(f.file, fp)
    dst = os.path.join(core.MEDIA, "t%d_final.mp3" % tid)
    ok, err = core.to_mp3(raw, dst)
    try:
        os.remove(raw)
    except Exception:
        pass
    if not ok:
        return {"ok": 0, "msg": "录音没处理好，再念一次"}
    core.ex("UPDATE threads SET audio_out=?, status='paid', paid_at=? WHERE id=?",
            (os.path.basename(dst), core.now(), tid))
    return {"ok": 1, "url": "/xin/m/" + os.path.basename(dst),
            "dur": round(core.dur_of(dst), 1)}


@APP.post("/xin/api/merge")
async def api_merge(req: Request):
    d = await req.json()
    tid = int(d.get("id", 0))
    r = core.one("SELECT * FROM threads WHERE id=?", (tid,))
    if not r:
        return {"ok": 0, "msg": "没有这一单"}
    # 代读：直接用客户上传的成品？不——代读也要博主念。统一走段录音。
    parts = []
    i = 1
    while True:
        p = os.path.join(core.MEDIA, "t%d_s%03d.mp3" % (tid, i))
        if not os.path.exists(p):
            break
        parts.append(p)
        i += 1
    if not parts:
        return {"ok": 0, "msg": "还没录"}
    out = os.path.join(core.MEDIA, "t%d_final.mp3" % tid)
    ok, err = core.concat_mp3(parts, out)
    if not ok:
        return {"ok": 0, "msg": "合成失败：%s" % err[-60:]}
    core.ex("UPDATE threads SET audio_out=?, status='paid', paid_at=? WHERE id=?",
            (os.path.basename(out), core.now(), tid))
    return {"ok": 1, "url": "/xin/m/" + os.path.basename(out), "n": len(parts)}


@APP.post("/xin/api/send")
async def api_send(req: Request):
    d = await req.json()
    tid = int(d.get("id", 0))
    r = core.one("SELECT * FROM threads WHERE id=?", (tid,))
    if not r:
        return {"ok": 0, "msg": "没有这一单"}
    token = r["token"] or core.new_token()
    core.ex("UPDATE threads SET token=?, status='done', done_at=? WHERE id=?",
            (token, core.now(), tid))
    return {"ok": 1, "page": "/xin/c/" + token}


# ---------------------------------------------------------------- 运营看板
def _wait_h(t):
    try:
        ts = time.mktime(time.strptime(t, "%Y-%m-%d %H:%M:%S"))
    except Exception:
        return 0
    return (time.time() - ts) / 3600.0


def _wait_txt(t):
    h = _wait_h(t)
    if h < 1:
        return "刚收到 " + (t[11:16] if len(t) > 16 else "")
    if h < 24:
        return "等了 %d 小时" % int(h)
    return "等了 %d 天" % int(h // 24)


@APP.get("/xin/ops/{key}", response_class=HTMLResponse)
def ops(key: str):
    okey = core.get("ops_key")
    if not okey or key != okey:
        return HTMLResponse("<h2 style='font-family:sans-serif'>链接不对</h2>", status_code=403)
    m = time.strftime("%Y-%m")
    rows = core.q("SELECT kind,price,created FROM threads WHERE status IN ('paid','done') AND created LIKE ?",
                  (m + "%",))
    cnt = len(rows)
    total = sum(r["price"] for r in rows)
    fee = int(round(total * 0.1))
    reply_n = sum(1 for r in rows if r["kind"] == "reply")
    brk = "回信 %d 单 · 代读 %d 单 · 平均每单 %d 元" % (
        reply_n, cnt - reply_n, int(total / cnt) if cnt else 0)

    todo = core.q("SELECT * FROM threads WHERE status='pending' ORDER BY id")
    if todo:
        parts = []
        for r in todo:
            h = _wait_h(r["created"])
            cls = "style='color:#A2503F;font-weight:600'" if h >= 24 else ""
            kind = "回信" if r["kind"] == "reply" else "代读"
            nick = r["nick"] or "没留名"
            parts.append(
                "<div style=\"display:flex;justify-content:space-between;gap:10px;"
                "padding:11px 0;border-bottom:1px dashed #E6E0D4;font-size:15px\">"
                "<span>%s · %s</span><span %s>%s<br><span style='font-size:12px;color:#8C8478'>￥%d</span></span></div>"
                % (kind, _esc(nick), cls, _wait_txt(r["created"]), r["price"]))
        todo_html = "".join(parts)
    else:
        todo_html = '<div class="empty">没有积压</div>'

    # 近 14 天
    days = []
    for i in range(13, -1, -1):
        d = time.strftime("%Y-%m-%d", time.localtime(time.time() - i * 86400))
        n = core.q("SELECT COUNT(*) c FROM threads WHERE status IN ('paid','done') AND created LIKE ?", (d + "%",))
        days.append((d[5:], n[0]["c"] if n else 0))
    mx = max([x[1] for x in days] + [1])
    bars = ""
    for d, n in days:
        hgt = int(6 + (n / mx) * 54)
        col = "#8A6E4B" if n else "#E6E0D4"
        bars += ("<div style='flex:1;text-align:center'>"
                 "<div style='height:%dpx;background:%s;border-radius:3px 3px 0 0'></div>"
                 "<div style='font-size:9px;color:#8C8478;margin-top:4px'>%s</div>"
                 "<div style='font-size:10px;color:#4A443C'>%s</div></div>"
                 % (hgt, col, d[3:], n if n else ""))
    bars = ("<div style='display:flex;align-items:flex-end;gap:3px;height:92px'>%s</div>" % bars)

    recent = core.q("SELECT * FROM threads WHERE status IN ('paid','done') ORDER BY id DESC LIMIT 20")
    if recent:
        rp = []
        for r in recent:
            kind = "回信" if r["kind"] == "reply" else "代读"
            rp.append("<div style='display:flex;justify-content:space-between;padding:9px 0;"
                      "border-bottom:1px solid #F0EBE1;font-size:14px;color:#4A443C'>"
                      "<span>%s · %s</span><span>￥%d · %s</span></div>"
                      % (kind, _esc(r["nick"] or "没留名"), r["price"], _age(r["created"])))
        recent_html = "".join(rp)
    else:
        recent_html = '<div class="empty">还没有交付</div>'

    html = ui.ops_page({
        "CSS": ui.DESK_CSS,
        "CNT": cnt, "TOTAL": total, "FEE": fee, "BREAK": brk,
        "TODO_N": len(todo), "TODO": todo_html,
        "BARS": bars, "RECENT": recent_html, "OPSKEY": okey,
    })
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


# ---------------------------------------------------------------- 交付页
@APP.get("/xin/c/{token}", response_class=HTMLResponse)
def deliver(token: str):
    r = core.one("SELECT * FROM threads WHERE token=?", (token,))
    if not r:
        return HTMLResponse(
            "<!DOCTYPE html><html><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<style>body{background:#FBF8F2;font-family:serif;color:#8C8274;"
            "display:flex;align-items:center;justify-content:center;height:100vh;margin:0;"
            "text-align:center;line-height:2}</style></head><body>"
            "<div>这封信不在<br><span style='font-size:13px'>可能已经过期了</span></div>"
            "</body></html>", status_code=404)
    player = ""
    if r["audio_out"]:
        player = ui.PLAYER_HTML.replace("@@URL@@", "/xin/m/" + r["audio_out"])
    body = _esc(r["final_text"] or r["draft"] or "")
    html = ui.deliver_page({
        "TITLE": "给你的回信",
        "CSS": ui.DE_CSS,
        "BRAND": core.get("brand") + " · 给你的一封回信",
        "PLAYER": player,
        "BODY": body,
        "TEXT_AFTER": "",
        "SIGN": core.get("brand"),
        "SIGNSUB": time.strftime("%Y 年 %m 月 %d 日", time.strptime(r["done_at"] or r["created"], "%Y-%m-%d %H:%M:%S")),
        "SCRIPT": ui.PLAYER_JS if player else "",
    })
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


# ---------------------------------------------------------------- 工具
def _split_text(t):
    """把一封信切成适合朗读的段：按句末标点，超长再按逗号"""
    t = (t or "").strip()
    if not t:
        return []
    t = re.sub(r"[ \t]*\n[ \t]*", "", t)
    raw = re.split(r"(?<=[。！？!?；;])", t)
    out, buf = [], ""
    for s in raw:
        s = s.strip()
        if not s:
            continue
        if len(buf) + len(s) <= 46:
            buf += s
        else:
            if buf:
                out.append(buf)
            while len(s) > 46:
                cut = max(s.rfind("，", 0, 46), s.rfind("、", 0, 46), s.rfind(",", 0, 46))
                if cut < 10:
                    cut = 46
                out.append(s[:cut + 1])
                s = s[cut + 1:]
            buf = s
    if buf:
        out.append(buf)
    # 合并过短的段
    merged = []
    for s in out:
        if merged and len(s) < 12:
            merged[-1] += s
        else:
            merged.append(s)
    return merged


@APP.get("/")
def root():
    return RedirectResponse("/xin/", status_code=302)


# ---- 数字分身聊天（2026-11-15）
try:
    import chat
    chat.install(APP)
except Exception as _e:
    print("[chat] mount failed:", _e)


# ---- 账户 / 余额 / 充值（2026-11-15）
try:
    import acct
    acct.install(APP)
except Exception as _e:
    print("[acct] mount failed:", _e)


# ---- 真人预约（2026-11-15）
try:
    import live
    live.install(APP)
except Exception as _e:
    print("[live] mount failed:", _e)


# ---- 老师首页 + 通话页（2026-11-15）
try:
    import boss
    boss.install(APP)
except Exception as _e:
    print("[boss] mount failed:", _e)


# ---- 网页通话（2026-11-15）
try:
    import call
    call.install(APP)
except Exception as _e:
    print("[call] mount failed:", _e)


# ---- 货架与设置（2026-11-15）
try:
    import shop
    shop.install(APP)
except Exception as _e:
    print("[shop] mount failed:", _e)


# ---- 一按就进（2026-11-16）----
@APP.get("/xin/w")
def _quick_in(request: Request):
    """最短的一条路：点一下就进工作台，顺手把这台设备记住。"""
    k = core.get("ops_key") or ""
    if not k:
        return RedirectResponse("/xin/", status_code=302)
    resp = RedirectResponse("/xin/boss/" + k, status_code=302)
    try:
        _g.remember(resp)
    except Exception:
        pass
    return resp


# ---- 画廊（2026-11-16）
try:
    import art
    art.install(APP)
except Exception as _e:
    print("[art] mount failed:", _e)


# ---- 静态资源（TRTC SDK）
try:
    from fastapi.staticfiles import StaticFiles
    APP.mount("/xin/static", StaticFiles(directory=os.path.join(core.BASE, "static")), name="xstatic")
except Exception as _e:
    print("[static] mount failed:", _e)

# ---- 作品图片目录（media/art/，供画廊用）
try:
    from fastapi.staticfiles import StaticFiles as _SF
    APP.mount("/xin/m/art", _SF(directory=os.path.join(core.MEDIA, "art")), name="xartimg")
except Exception as _e:
    print("[art-img] mount failed:", _e)
