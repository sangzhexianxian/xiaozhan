# -*- coding: utf-8 -*-
"""夜话 · 老师手机第一屏 + 通话页
挂载：app.py 末尾  import boss; boss.install(APP)
"""
import sqlite3
import time

import core
import acct
import live
import conf


def _c():
    c = sqlite3.connect(core.DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    c = _c()
    for col, ddl in (("start_at", "TEXT DEFAULT ''"), ("end_at", "TEXT DEFAULT ''"),
                     ("secs", "INTEGER DEFAULT 0"), ("note", "TEXT DEFAULT ''")):
        try:
            c.execute("ALTER TABLE booking ADD COLUMN %s %s" % (col, ddl))
        except Exception:
            pass
    c.commit()
    c.close()


init()


def boss_state():
    today = time.strftime("%Y-%m-%d")
    c = _c()
    pay = c.execute("SELECT COUNT(*) n, SUM(amount) s FROM ord WHERE status='claimed'").fetchone()
    bk = c.execute("""SELECT b.*, u.nick, u.phone FROM booking b LEFT JOIN usr u ON u.id=b.uid
                      WHERE b.status='booked' ORDER BY b.slot""").fetchall()
    mail = c.execute("SELECT COUNT(*) n FROM threads WHERE status IN ('pending','claimed')").fetchone()["n"]
    c.close()
    todo = [dict(r) for r in bk]
    tdy = [r for r in todo if (r["slot"] or "")[:10] == today]
    nxt = None
    now = time.time()
    for r in todo:
        try:
            if time.mktime(live._dt(r["slot"])) >= now - 1800:
                nxt = r
                break
        except Exception:
            pass
    c = _c()
    dn = c.execute("""SELECT COUNT(*) n, COALESCE(SUM(secs),0) secs,
                             COALESCE(SUM(amount),0) amt FROM booking
                      WHERE status='done' AND (substr(COALESCE(done_at,''),1,10)=?
                            OR substr(COALESCE(slot,''),1,10)=?)""",
                   (today, today)).fetchone()
    rec = c.execute("""SELECT note, slot FROM booking WHERE COALESCE(note,'')<>''
                       ORDER BY id DESC LIMIT 2""").fetchall()
    c.close()
    art_n = 0
    try:
        import art as _art
        _c2 = _art._db()
        art_n = _c2.execute(
            "SELECT COUNT(*) n FROM art_ord WHERE status='claimed'").fetchone()["n"] or 0
        _c2.close()
    except Exception:
        pass

    return {"art_n": art_n, "recent": [dict(x) for x in rec],
            "pay_n": pay["n"] or 0, "pay_s": round(pay["s"] or 0, 0),
            "today_n": len(tdy), "next": nxt, "mail_n": mail,
            "tdy": tdy, "done_n": dn["n"] or 0,
            "done_min": int((dn["secs"] or 0) / 60),
            "done_amt": round(dn["amt"] or 0, 0)}


def wx():
    return core.get("live_wx") or ""


CSS = """
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;-webkit-text-size-adjust:100%}
body{background:#FBFAF7;color:#23201C;font-family:-apple-system,"PingFang SC","Noto Sans CJK SC",sans-serif;
 line-height:1.75;padding:30px 20px 50px;min-height:100vh}
.wrap{max-width:430px;margin:0 auto}
.head{text-align:center;margin-bottom:30px}
.head img{width:76px;height:76px;border-radius:50%;object-fit:cover;
 box-shadow:0 0 0 1px rgba(138,110,75,.22);margin-bottom:12px}
.nm{font-size:20px;letter-spacing:.12em;font-family:"Songti SC","Noto Serif CJK SC",serif}
.st{font-size:12.5px;color:#8C8478;letter-spacing:.14em;margin-top:5px}
.card{display:flex;align-items:center;background:#fff;border:1px solid #E9E3D7;border-radius:14px;
 padding:24px 18px;margin-bottom:13px;text-decoration:none;color:inherit;
 box-shadow:0 2px 10px rgba(120,100,70,.05)}
.card .bar{width:4px;align-self:stretch;border-radius:2px;margin-right:16px}
.b1{background:#C08A2E}.b2{background:#4A7C59}.b3{background:#8A6E4B}
.card .t{flex:1}
.card b{display:block;font-size:20px;letter-spacing:.05em;font-weight:600}
.card span{display:block;font-size:13.5px;color:#8C8478;margin-top:6px}
.card .n{font-size:26px;color:#C08A2E;font-weight:300;letter-spacing:.02em;text-align:right}
.card .n.zero{color:#CFC8BB}
.card .n.zero small{color:#D8D2C6}
.card .n small{display:block;font-size:11px;color:#ADA395;letter-spacing:.1em}
.card.hot{border-color:#D9B96E;background:#FFFDF8}
.card.hot b{color:#A5761F}
.card.now{border-color:#4A7C59;background:#FBFFFC;box-shadow:0 4px 18px rgba(74,124,89,.13)}
.card.now b{color:#2F5A3A}
.card.now .big2{display:block;margin-top:7px;color:#4A7C59;font-size:14px;font-weight:600;
 letter-spacing:.06em}
.dim{opacity:.55}
.ghost{display:block;text-align:center;font-size:15px;color:#8A6E4B;text-decoration:none;
 padding:15px;border:1px solid #E9E3D7;border-radius:12px;background:#fff;letter-spacing:.1em;margin-top:22px}
.set{margin-top:28px;font-size:12.5px;color:#8C8478;line-height:2}
.set input{width:100%;margin-top:8px;padding:12px 13px;border:1px solid #E9E3D7;border-radius:10px;
 font-family:inherit;font-size:15px;background:#fff;outline:none}
.set button{margin-top:9px;width:100%;padding:12px;border:0;border-radius:10px;background:#8A6E4B;
 color:#fff;font-family:inherit;font-size:14.5px;letter-spacing:.1em;cursor:pointer}
.foot{text-align:center;font-size:11.5px;color:#B8AF9F;letter-spacing:.14em;margin-top:36px}
/* 通话页 */
.room{max-width:430px;margin:0 auto}
.rt{text-align:center;font-size:15px;color:#8C8478;letter-spacing:.1em}
.rt b{display:block;font-size:24px;color:#23201C;margin:8px 0;font-family:"Songti SC",serif}
.clock{text-align:center;font-size:52px;font-weight:200;letter-spacing:.06em;color:#C08A2E;margin:26px 0 8px;
 font-variant-numeric:tabular-nums}
.cl2{text-align:center;font-size:13px;color:#8C8478;margin-bottom:26px}
.big{display:block;width:100%;padding:19px;border:0;border-radius:14px;font-family:inherit;
 font-size:18px;font-weight:600;letter-spacing:.12em;cursor:pointer;margin-bottom:12px}
.gold{background:#C08A2E;color:#fff}
.dark{background:#3E3830;color:#fff}
.line{background:#fff;border:1px solid #E9E3D7;color:#8A6E4B;font-size:15px;font-weight:400;padding:15px}
.wxbox{background:#fff;border:1px solid #E9DCC0;border-radius:14px;padding:20px;text-align:center;margin:20px 0}
.wxbox .k{font-size:12.5px;color:#8C8478;letter-spacing:.1em;margin-bottom:10px}
.wxbox .v{font-size:26px;letter-spacing:.1em;color:#23201C;font-weight:600;word-break:break-all}
.wxbox .c{margin-top:12px;display:inline-block;background:#8A6E4B;color:#fff;border-radius:8px;
 padding:10px 22px;font-size:14px;letter-spacing:.1em;cursor:pointer}
.tip{font-size:12.5px;color:#8C8478;line-height:1.95;margin-top:16px;text-align:center}
.tip b{color:#A5761F}
textarea{width:100%;min-height:88px;margin-top:10px;padding:13px;border:1px solid #E9E3D7;border-radius:10px;
 font-family:inherit;font-size:15px;background:#fff;outline:none;resize:vertical}
"""

ROOM_CSS = """
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:#0B0A08;color:#F2ECDF;
 font-family:"Songti SC","Noto Serif CJK SC","Source Han Serif SC",Georgia,serif;
 font-size:17px;line-height:1.9;letter-spacing:.02em;
 padding:calc(38px + env(safe-area-inset-top)) 26px calc(64px + env(safe-area-inset-bottom));
 max-width:580px;margin:0 auto;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}

/* ---- 抬头 ---- */
.top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:52px}
.brand{display:flex;align-items:center;gap:17px}
.seal{width:46px;height:46px;border-radius:23px;border:1px solid rgba(201,169,97,.34);
 display:flex;align-items:center;justify-content:center;font-size:20px;
 color:#B09154;flex:0 0 auto;letter-spacing:0}
.tg{font-size:25px;letter-spacing:.26em;color:#F7F2E6;line-height:1.3;font-weight:600}
.tg small{display:block;font-size:13px;letter-spacing:.5em;color:#A87F4A;
 margin-top:9px;font-weight:400}
.dt{text-align:right;font-size:12.5px;color:#948C7B;line-height:2}
.dt b{color:#F2ECDF;font-weight:400}
.clock{font-size:19px;color:#C9A961;letter-spacing:.08em}

/* ---- 章节标题：一 · 今 天 ---- */
.todo{display:block;margin:0 0 30px;padding:19px 20px;border-radius:4px;
 background:rgba(201,169,97,.1);border:1px solid rgba(201,169,97,.4)}
.todo b{display:block;font-size:19px;color:#E6CD91;font-weight:400;letter-spacing:.1em}
.todo span{display:block;font-size:14.5px;color:#A79E8B;margin-top:5px}

.pch{font-size:14px;color:#A87F4A;letter-spacing:.32em;
 margin:0 0 4px;font-weight:400}
.pch em{font-style:normal;color:#5C4A2C;margin-right:12px}
.rule{height:1px;background:linear-gradient(90deg,rgba(201,169,97,.5),rgba(201,169,97,.05));
 margin:0 0 22px}
.sec{margin-bottom:48px}

/* ---- 今天 ---- */
.prog{margin-bottom:2px}
.pr{display:flex;align-items:center;gap:14px;padding:19px 0;
 border-bottom:1px solid rgba(201,169,97,.1)}
.pr:last-child{border-bottom:none}
.pr b{font-size:21px;color:#F4EFE2;font-weight:400;letter-spacing:.06em;flex:0 0 auto}
.pr i{flex:1;font-style:normal;font-size:16.5px;color:#A79E8B;line-height:1.7}
.pr i small{display:block;font-size:15px;color:#8F8776;margin-top:3px}
.pr em{font-style:normal;font-size:14px;color:#C9A961;letter-spacing:.05em}
.pr.now b{color:#E6CD91}
.empty{padding:22px 0;font-size:18px;color:#8F8776;line-height:2}
.empty b{font-size:22px;color:#6B6355;font-weight:400}
.empty small{display:block;font-size:15px;color:#6B6355;margin-top:8px}

/* ---- 四行大名单 ---- */
.btns{border:1px solid rgba(201,169,97,.22);border-radius:4px;overflow:hidden}
.b{display:flex;align-items:center;gap:15px;padding:22px 20px;
 border-bottom:1px solid rgba(201,169,97,.14);min-height:76px}
.b:last-child{border-bottom:none}
.b u{text-decoration:none;font-size:22px;opacity:.75;flex:0 0 auto}
.b b{font-size:20px;color:#F2ECDF;font-weight:400;letter-spacing:.14em;flex:0 0 auto}
.b span{flex:1;font-size:16.5px;color:#A79E8B;text-align:right}
.b s{text-decoration:none;font-size:26px;color:#C9A961;
 font-weight:400;min-width:34px;text-align:right;flex:0 0 auto}
.b.on s{color:#E6A94D}
.b.on b{color:#F4EFE2}

/* ---- 给粉丝的链接 ---- */
.lnks{border:1px solid rgba(201,169,97,.22);border-radius:4px;overflow:hidden}
.lk{display:flex;align-items:center;gap:16px;padding:20px;
 border-bottom:1px solid rgba(201,169,97,.14);min-height:88px}
.lk:last-child{border-bottom:none}
.lk .lt{flex:1;min-width:0}
.lk b{display:block;font-size:19px;color:#F2ECDF;font-weight:400;letter-spacing:.1em}
.lk i{display:block;font-style:normal;font-size:15.5px;color:#A79E8B;margin-top:5px}
.lk button{flex:0 0 auto;min-width:82px;height:52px;border-radius:3px;
 border:1px solid rgba(201,169,97,.5);background:transparent;color:#C9A961;
 font-family:inherit;font-size:16px;letter-spacing:.14em}
.lk button.on{border-color:rgba(120,200,155,.6);color:#8FD3AE}

/* ---- 两个设置 ---- */
.g2{display:flex;gap:14px}
.g2 a{flex:1;display:block;padding:26px 20px;border:1px solid rgba(201,169,97,.22);
 border-radius:4px;text-align:center}
.g2 b{display:block;font-size:18px;color:#F2ECDF;font-weight:400;letter-spacing:.16em}
.g2 span{display:block;font-size:15.5px;color:#A79E8B;margin-top:8px}

/* ---- 今日小结 ---- */
.sumh{font-size:14px;color:#A87F4A;letter-spacing:.32em;margin-bottom:4px}
.sum{display:flex;border:1px solid rgba(201,169,97,.22);border-radius:4px}
.si{flex:1;padding:26px 8px;text-align:center;border-right:1px solid rgba(201,169,97,.14)}
.si:last-child{border-right:none}
.si b{display:block;font-size:38px;color:#C9A961;font-weight:400;line-height:1.2}
.si span{display:block;font-size:15px;color:#A79E8B;margin-top:6px;letter-spacing:.14em}

/* ---- 开放时段 ---- */
.tip{font-size:15.5px;color:#948C7B;line-height:2.1;margin-top:14px}
.rec{padding:13px 0;border-bottom:1px solid rgba(201,169,97,.08);font-size:15px}
.rec i{font-style:normal;color:#C5BCA8;display:block}
.rec em{font-style:normal;font-size:13px;color:#6B6355}

/* ---- 通话入口 ---- */
.nx{display:block;margin:22px 0 0;padding:24px;text-align:center;
 border:1px solid rgba(201,169,97,.55);color:#E6CD91;font-size:19px;letter-spacing:.16em}

/* ---- 网站 ---- */
.site{margin:56px 0 0;text-align:center}
.site a{display:inline-block;font-size:15px;color:#8D6C42;letter-spacing:.2em;
 padding:14px 0;border-top:1px solid rgba(201,169,97,.18);min-width:70%}
.foot{font-size:14px;color:#6B6355;text-align:center;line-height:2;margin-top:22px}
.c{color:#C9A961}
.big{display:block;margin-top:26px;padding:22px;text-align:center;
 border:1px solid rgba(201,169,97,.5);color:#E6CD91;font-size:18px;letter-spacing:.14em}
.line{border-color:rgba(201,169,97,.28);color:#C9A961}
"""




def watch(request):
    """有人点开工作台就通知一声。同一个 IP 只报一次，避免刷屏。"""
    try:
        import json as _j
        import notify as _n

        ip = (request.headers.get("x-real-ip") or "").strip()
        if not ip:
            ip = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        if not ip and request.client:
            ip = request.client.host
        if not ip or ip in ("127.0.0.1", "103.236.93.55", "45.207.218.98"):
            return

        seen = []
        try:
            seen = _j.loads(core.get("seen_ips") or "[]")
        except Exception:
            pass
        if ip in seen:
            return

        ua = request.headers.get("user-agent") or ""
        if "iPhone" in ua:
            dev = "iPhone"
        elif "OpenHarmony" in ua:
            dev = "华为 · 鸿蒙"
        elif "Android" in ua:
            dev = "安卓手机"
        elif "iPad" in ua:
            dev = "iPad"
        elif "Macintosh" in ua:
            dev = "Mac 电脑"
        elif "Windows" in ua:
            dev = "Windows 电脑"
        else:
            dev = "不认识的设备"

        now = time.strftime("%m-%d %H:%M")
        html = ('<div style="font-family:-apple-system,\'PingFang SC\',sans-serif;'
                'max-width:520px;margin:0 auto;padding:10px">'
                '<h2 style="color:#8a6b32">有人点开了工作台</h2>'
                '<p style="background:#f6f2ea;padding:14px;border-radius:8px;'
                'color:#2b2b2b;line-height:2.1">'
                ' 时间：<b>' + now + '</b><br>'
                ' 设备：<b>' + dev + '</b><br>'
                ' IP：' + ip + '<br>'
                ' 浏览器：' + ua[:70] +
                '</p>'
                '<p style="font-size:13px;color:#666">'
                '如果这不是你自己在测，那就是老师点开了 —— '
                '可以问一句「刚点开看到了吗」。</p>'
                '<p><a href="' + conf.u("/xin/boss/")
                + (core.get("ops_key") or "") + '">看工作台 ›</a></p></div>')

        _n.alert("有人点开了工作台（" + dev + "）", html,
                 "有人点开了工作台\n时间 " + now + "\n设备 " + dev + "\nIP " + ip)

        seen.append(ip)
        core.set("seen_ips", _j.dumps(seen[-300:], ensure_ascii=False))
    except Exception as e:
        print("[watch]", e)


def install(app):
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    def _ok(key):
        return bool(key) and key == core.get("ops_key")

    @app.get("/xin/boss/{key}", response_class=HTMLResponse)
    def _boss(key: str, request: Request):
        if not _ok(key):
            return HTMLResponse("<h2>没有入口</h2>", status_code=403)
        try:
            watch(request)
        except Exception:
            pass
        try:
            core.set("boss_seen", str(time.time()))
        except Exception:
            pass
        st = boss_state()
        nxt = st["next"]
        now = time.time()
        hh = int(time.strftime("%H"))
        seg = "早" if hh < 11 else ("午" if hh < 17 else ("夜" if hh < 23 else "深夜"))
        today = time.strftime("%-m月%-d日")
        wd = "周" + "日一二三四五六"[int(time.strftime("%w"))]

        h = ['<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
             '<title>值班室</title><style>' + ROOM_CSS + '</style></head><body><div class="wrap">']

        # 抬头：印章「山」+ 品牌 + 工作台
        h.append('<div class="top">'
                 '<div class="brand">'
                 '<div class="seal">\u5c71</div>'
                 '<div><div class="tg">\u91ce\u5c71\u4e0b\u7684\u5c0f\u7ad9'
                 '<small>\u5de5 \u4f5c \u53f0</small></div></div></div>'
                 '<div class="dt"><span class="clock" id="ck">%s</span> \u00b7 <b>%s</b>'
                 '<br>%s \u00b7 %s</div></div>'
                                  % (time.strftime("%H:%M"), seg, today, wd))

        # 今天节目单
        _pn0 = st["pay_n"] + st.get("art_n", 0)
        if _pn0:
            h.append('<a class="todo" href="/xin/pay/%s">'
                     '<b>有 %d 笔钱等你确认</b>'
                     '<span>点这里看一眼，收到了再点确认 ›</span></a>'
                     % (key, _pn0))

        h.append('<div class="pch"><em>一</em>今 天</div>'
                 '<div class="rule"></div><div class="prog">')
        if st["tdy"]:
            for r in st["tdy"]:
                hm = (r["slot"] or "")[11:16]
                dm = int((time.mktime(live._dt(r["slot"])) - now) / 60)
                if dm > 1:
                    tip = "%d 分钟后" % dm
                elif dm > -3:
                    tip = "就是现在"
                else:
                    tip = "已过"
                cls = " now" if r is nxt else ""
                tp = (r["topic"] if "topic" in r.keys() else "") or ""
                extra = ("　<i style=\"font-style:normal;color:#C9A961;font-size:12px\">"
                         "「" + tp[:26] + "」</i>") if tp else ""
                h.append('<div class="pr%s"><b>%s</b><i>%s · %s<small>%d 分钟%s</small></i>'
                         '<em>%s</em></div>'
                         % (cls, hm, r["nick"] or "对方", live.LABEL.get(r["kind"], ""),
                            r["minutes"] or 20, extra, tip))
        elif nxt:
            sl = (nxt["slot"] or "")
            h.append('<div class="pr"><b>%s</b><i>%s · %s'
                     '<small>下一场 · %s</small></i><em></em></div>'
                     % (sl[11:16] if sl[11:16] else "—",
                        nxt["nick"] or "对方", live.LABEL.get(nxt["kind"], ""),
                        sl[5:10].replace("-", "/")))
        else:
            h.append('<div class="pr empty"><b>—</b><i>这 几 日 无 约<small>'
                     '可 歇 息 ， 也 可 调 价</small></i><em></em></div>')
        h.append('</div>')

        if st["recent"]:
            h.append('<div class="pch">最 近 说 过 的</div>')
            for r in st["recent"]:
                h.append('<div class="rec"><i>%s</i><em>%s</em></div>'
                         % (r["note"], (r["slot"] or "")[5:10].replace("-", "/")))

        # 进通话（只在有下一场时出现）
        if nxt:
            dm = int((time.mktime(live._dt(nxt["slot"])) - now) / 60)
            if -30 <= dm <= 60:
                h.append('<a class="nx" href="/xin/room/%s/%s">进 通 话 页 · %s</a>'
                         % (key, nxt["id"], nxt["nick"] or "对方"))

        # 三个大按钮
        h.append('<div class="btns">')
        h.append('<a class="b" href="/xin/liveops/%s"><s%s>%d</s><b>有 约</b>'
                 '<span>%s</span></a>'
                 % (key, ' class="on"' if st["today_n"] else "", st["today_n"],
                    "今天 %d 个约" % st["today_n"]))
        _pn = st["pay_n"] + st.get("art_n", 0)
        h.append('<a class="b" href="/xin/pay/%s"><s%s>%d</s><b>有 钱</b>'
                 '<span>%s</span></a>'
                 % (key, ' class="on"' if _pn else "", _pn,
                    "%d 笔待确认" % _pn))
        h.append('<a class="b" href="/xin/chatlog/%s"><s%s>%d</s><b>有 话</b>'
                 '<span>%s</span></a>'
                 % (key, ' class="on"' if st["mail_n"] else "", st["mail_n"],
                    "%d 条待听" % st["mail_n"]))
        h.append('</div>')

        # 给粉丝的链接（一键复制）
        _base = conf.SITE
        h.append('<div class="pch"><em>二</em>链 接</div>'
                 '<div class="rule"></div><div class="lnks">')
        _links = [
            ("门厅", "请他们先进这里", _base + "/xin/"),
            ("约真人", "挑时间 · 电话或视频", _base + "/xin/live"),
            ("写封信", "写一封 · 他念给你听", _base + "/xin/liuyan"),
            ("我 的", "余额 · 充值 · 记录", _base + "/xin/me"),
            ("画 廊", "十三幅画 · 看中了跟他聊", _base + "/xin/art"),
        ]
        if nxt and nxt["token"]:
            _links.append(("通话门牌",
                           "%s · %s" % (nxt["nick"] or "对方",
                                        (nxt["slot"] or "")[5:16].replace("-", "/")),
                           _base + "/xin/join/" + nxt["token"]))
        for _nm, _sub, _u in _links:
            h.append('<div class="lk"><div class="lt"><b>%s</b><i>%s</i></div>'
                     '<button onclick="cp(this, this.dataset.u)" data-u="%s">复制</button></div>'
                     % (_nm, _sub, _u))
        h.append('</div>')
        h.append('<a href="/xin/artops/%s" style="display:block;margin-top:14px;'
                 'padding:24px;border:1px solid rgba(201,169,97,.22);border-radius:4px;'
                 'text-align:center"><b style="display:block;font-size:18px;color:#F2ECDF;'
                 'font-weight:400;letter-spacing:.16em">画 廊</b>'
                 '<span style="display:block;font-size:15.5px;color:#A79E8B;margin-top:8px">'
                 '改价 · 标已售 · 上下架</span></a>' % key)
        h.append('<a href="/xin/artpay/%s" style="display:block;margin-top:12px;'
                 'padding:22px;border:1px solid rgba(201,169,97,.22);border-radius:4px;'
                 'text-align:center"><b style="display:block;font-size:17px;color:#F2ECDF;'
                 'font-weight:400;letter-spacing:.14em">画 的 订 单</b>'
                 '<span style="display:block;font-size:15px;color:#A79E8B;margin-top:7px">'
                 '谁付了钱 · 你说收到没</span></a>' % key)

        # 今日小结
        h.append('<div class="sumh"><em>三</em>归 账</div>'
                 '<div class="rule"></div><div class="sum">')
        h.append('<div class="si"><b>%d</b><span>场</span></div>' % st["done_n"])
        h.append('<div class="si"><b>%s</b><span>分钟</span></div>'
                 % (st["done_min"] or "\u2014"))
        h.append('<div class="si"><b>%d</b><span>元</span></div>' % int(st["done_amt"]))
        h.append('</div>')

        # 两个日常入口：放上面，别藏在页脚
        h.append('<div class="pch"><em>四</em>设 置</div><div class="rule"></div>')
        _dk = core.get("desk_key") or ""
        _box = ('display:block;flex:1;padding:15px 14px;border-radius:14px;text-decoration:none;'
                'border:1px solid rgba(201,169,97,.32);background:rgba(201,169,97,.075)')
        _b = 'display:block;font-size:15px;letter-spacing:.14em;color:#F0E4CB;font-weight:500'
        _sp = 'display:block;font-size:11.5px;color:#8C8170;margin-top:4px;letter-spacing:.04em'
        h.append('<div style="display:flex;gap:10px;margin-top:13px">')
        h.append('<a href="/xin/setup/%s" style="%s">'
                 '<b style="%s">价格与时间</b><span style="%s">改价 · 开放时段</span></a>'
                 % (key, _box, _b, _sp))
        if _dk:
            h.append('<a href="/xin/d/%s" style="%s">'
                     '<b style="%s">信 箱</b><span style="%s">写回信 · 录音</span></a>'
                     % (_dk, _box, _b, _sp))
        h.append('</div>')

        # 我开放的时段
        try:
            cf = live.cfg()
            wdn = ["日", "一", "二", "三", "四", "五", "六"]
            ds = " ".join("周" + wdn[int(x)] for x in cf["days"])
            ts = " · ".join(cf["times"])
            h.append('<div class="foot">我开放的是 <b style="color:#C9A961">%s</b><br>%s　'
                     '<a href="/xin/setup/%s">改 ›</a></div>' % (ds, ts, key))
        except Exception:
            pass

        # 页脚
        wv = wx()
        if not wv:
            h.append('<div class="foot" style="color:#8A6B3A">还没填微信号，'
                     '粉丝没法加你　<a href="/xin/setup/%s">去填 ›</a></div>' % key)
        h.append('<div class="site"><a href="' + conf.SITE + '" target="_blank">'
                 '我的网站 ↗</a></div>')

        h.append('<script>'
                 'function cp(b,u){'
                 'function done(){b.textContent="已复制";b.className="on";'
                 'setTimeout(function(){b.textContent="复制";b.className=""},1700)}'
                 'function fb(){var a=document.createElement("textarea");a.value=u;'
                 'a.style.cssText="position:fixed;top:0;left:0;opacity:0";'
                 'document.body.appendChild(a);a.select();'
                 'try{document.execCommand("copy");done()}catch(e){'
                 'b.textContent="长按";setTimeout(function(){b.textContent="复制"},2200)}'
                 'a.parentNode.removeChild(a)}'
                 'if(navigator.clipboard&&location.protocol==="https:"){'
                 'navigator.clipboard.writeText(u).then(done,fb)}else{fb()}}'
                 'var P=function(n){return (n<10?"0":"")+n};'
                 'function ck(){var d=new Date(),e=document.getElementById("ck");'
                 'if(e)e.textContent=P(d.getHours())+":"+P(d.getMinutes());}'
                 'ck();setInterval(ck,20000);'
                 '</script>')
        h.append('</div><script>try{var p=location.pathname;if(/^\/xin\/(boss|setup|pay|orders|liveops|chatlog)\//.test(p))history.replaceState(null,\'\',\'/xin/b\');}catch(e){}</script></body></html>')
        from fastapi.responses import HTMLResponse as _HR
        return _HR("".join(h), headers={"Cache-Control": "no-store, must-revalidate"})

    @app.post("/xin/api/boss/wx")
    async def _boss_wx(req: Request):
        d = await req.json()
        if not _ok(d.get("key") or ""):
            return {"ok": 0, "msg": "没有权限"}
        v = (d.get("wx") or "").strip()[:40]
        if not v:
            return {"ok": 0}
        core.set("live_wx", v)
        return {"ok": 1}

    @app.get("/xin/room/{key}/{bid}", response_class=HTMLResponse)
    def _room(key: str, bid: int):
        if not _ok(key):
            return HTMLResponse("<h2>没有入口</h2>", status_code=403)
        c = _c()
        r = c.execute("""SELECT b.*, u.nick, u.phone FROM booking b
                         LEFT JOIN usr u ON u.id=b.uid WHERE b.id=?""", (bid,)).fetchone()
        prev = None
        if r:
            prev = c.execute("""SELECT note,slot FROM booking WHERE uid=? AND status='done'
                                AND note<>'' ORDER BY id DESC LIMIT 1""", (r["uid"],)).fetchone()
        c.close()
        if not r:
            return HTMLResponse("<h2>没有这一场</h2>", status_code=404)

        t0 = time.mktime(live._dt(r["slot"]))
        now = time.time()
        dm = (t0 - now) / 60.0
        started = bool(r["start_at"])
        ended = bool(r["end_at"])

        h = ['<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
             '<title>跟%s说话</title><style>' % (r["nick"] or "对方") + CSS + '</style>',
             '</head><body><div class="room">',
             '<div class="rt">%s<b>%s</b>%s</div>'
             % ((r["slot"] or "")[5:16], r["nick"] or "对方",
                live.LABEL.get(r["kind"], "") + "　" + (r["phone"] or "")[-4:])]

        if ended:
            mins = int((r["secs"] or 0) / 60)
            h.append('<div class="clock">%d:00</div><div class="cl2">这场聊完了</div>'
                     '<a class="big line" href="/xin/boss/%s">回到首页</a>' % (mins, key))
        elif started:
            st = time.mktime(time.strptime(r["start_at"], "%Y-%m-%d %H:%M:%S"))
            el = int(now - st)
            h.append('<div class="clock" id="ck">%02d:00</div>' % (el // 60))
            h.append('<div class="cl2">已经在说了</div>')
            h.append('<button class="big dark" id="end">聊 完 了</button>')
            h.append('<div id="note" style="display:none">'
                     '<div class="tip" style="text-align:left">'
                     '<b>这次她说的最要紧的一句</b>（下次她再约，会显示在这儿）'
                     '<textarea id="nt" placeholder="比如：儿子要中考，睡不着"></textarea>'
                     '<button class="big gold" id="saven" style="margin-top:10px">记 下 来</button></div></div>')
        elif dm > 15:
            w = wx()
            h.append('<div class="clock">%.0f:00</div><div class="cl2">%d 分钟后开始</div>'
                     % (dm, int(dm)))
            if w:
                h.append('<div class="wxbox"><div class="k">先把他加上，到点直接打</div>'
                         '<div class="v" id="wxv">%s</div>'
                         '<div class="c" id="cp">复制微信号</div>'
                         '<div class="k" style="margin-top:14px">加好友要等他通过<br>'
                         '现在加，到点正好</div></div>' % w)
            else:
                h.append('<div class="wxbox"><div class="k">还没填微信号</div>'
                         '<a class="c" href="/xin/boss/%s" style="text-decoration:none">去填</a></div>' % key)
            h.append('<a class="big line" href="/xin/boss/%s">先回去</a>' % key)
        else:
            w = wx()
            if w:
                h.append('<div class="wxbox"><div class="k">现在是他的微信</div>'
                         '<div class="v" id="wxv">%s</div>'
                         '<div class="c" id="cp">复制微信号</div>'
                         '<div class="k" style="margin-top:14px">打开微信，加他，打语音过去</div></div>' % w)
            else:
                h.append('<div class="wxbox"><div class="k">还没填微信号</div>'
                         '<div class="k">回首页填一下</div>'
                         '<a class="c" href="/xin/boss/%s" style="text-decoration:none">去填</a></div>' % key)
            if prev and prev["note"]:
                h.append('<div class="tip" style="text-align:left;background:#fff;border:1px solid #E9E3DC;'
                         'border-radius:12px;padding:13px 15px;margin:4px 0 18px">'
                         '<b>上次（%s）记下的</b><br>%s</div>'
                         % ((prev["slot"] or "")[5:10], prev["note"]))
            if core.get("trtc_appid") and core.get("trtc_ok"):
                h.append('<a class="big line" href="/xin/call/%s/%d" style="text-decoration:none;'
                         'text-align:center">在网页里直接接通</a>' % (key, bid))
            h.append('<button class="big gold" id="start">打 通 了，开 始 计 时</button>')
            h.append('<div class="tip">按了就开始算时间<br>聊完记得回来点「聊完了」</div>')

        h.append('</div><script>var KEY="%s",BID=%d;' % (key, bid))
        h.append("""
function api(p,o){return fetch(p,o?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o)}:{})
 .then(function(r){return r.json();});}
var cp=document.getElementById('cp');
if(cp) cp.onclick=function(){var v=document.getElementById('wxv').textContent;
 if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(v);}
 else{var t=document.createElement('textarea');t.value=v;document.body.appendChild(t);t.select();
 document.execCommand('copy');document.body.removeChild(t);}
 this.textContent='复制好了 ✓';};
var sb=document.getElementById('start');
if(sb) sb.onclick=function(){var b=this;b.disabled=true;api('/xin/api/room/start',{key:KEY,id:BID})
 .then(function(j){if(j.ok)location.reload();else{b.disabled=false;alert(j.msg||'没成功');}});};
var eb=document.getElementById('end');
if(eb) eb.onclick=function(){var b=this;b.disabled=true;
 api('/xin/api/room/end',{key:KEY,id:BID}).then(function(j){
  if(j.ok){document.getElementById('note').style.display='block';
   b.textContent='已停止计时';}
  else{b.disabled=false;alert(j.msg||'没成功');}});};
var sn=document.getElementById('saven');
if(sn) sn.onclick=function(){var v=document.getElementById('nt').value.trim();
 api('/xin/api/room/note',{key:KEY,id:BID,note:v}).then(function(j){
  if(j.ok)location.href='/xin/boss/'+KEY;else alert('没存上');});};
""")
        h.append('</script></body></html>')
        return "".join(h)

    @app.post("/xin/api/room/start")
    async def _r_start(req: Request):
        d = await req.json()
        if not _ok(d.get("key") or ""):
            return {"ok": 0, "msg": "没有权限"}
        bid = int(d.get("id") or 0)
        c = _c()
        r = c.execute("SELECT * FROM booking WHERE id=?", (bid,)).fetchone()
        if not r:
            c.close()
            return {"ok": 0, "msg": "没有这单"}
        if r["start_at"]:
            c.close()
            return {"ok": 1}
        c.execute("UPDATE booking SET start_at=? WHERE id=?", (core.now(), bid))
        c.commit()
        c.close()
        return {"ok": 1}

    @app.post("/xin/api/room/end")
    async def _r_end(req: Request):
        d = await req.json()
        if not _ok(d.get("key") or ""):
            return {"ok": 0, "msg": "没有权限"}
        bid = int(d.get("id") or 0)
        c = _c()
        r = c.execute("SELECT * FROM booking WHERE id=?", (bid,)).fetchone()
        if not r:
            c.close()
            return {"ok": 0, "msg": "没有这单"}
        if not r["start_at"]:
            c.close()
            return {"ok": 0, "msg": "还没点开始"}
        st = time.mktime(time.strptime(r["start_at"], "%Y-%m-%d %H:%M:%S"))
        secs = max(0, int(time.time() - st))
        c.execute("UPDATE booking SET end_at=?, secs=?, status='done', done_at=? WHERE id=?",
                  (core.now(), secs, core.now(), bid))
        c.commit()
        c.close()
        return {"ok": 1, "secs": secs}

    @app.post("/xin/api/room/note")
    async def _r_note(req: Request):
        d = await req.json()
        if not _ok(d.get("key") or ""):
            return {"ok": 0, "msg": "没有权限"}
        bid = int(d.get("id") or 0)
        note = (d.get("note") or "").strip()[:200]
        c = _c()
        c.execute("UPDATE booking SET note=? WHERE id=?", (note, bid))
        c.commit()
        c.close()
        return {"ok": 1}
