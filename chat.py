# -*- coding: utf-8 -*-
"""我的小站 · 数字分身聊天（测试版）
挂载方式：app.py 末尾  import chat; chat.install(APP)
"""
import json
import os
import sqlite3
import subprocess
import threading
import time

import core
import acct as _acct
import conf

PY = conf.PYBIN
GEN = os.environ.get("GEN_PODCAST", "")   # 可选：外部 TTS 脚本，不配则只回文字
VOICE = conf.VOICE_ID       # 老师（复刻声，同「时光绅士」那条线）
RATE = "-2"

FREE_N = 3                  # 免费试说 3 句（累计，一次性的）
PRICE_WEEK = 29.9           # 一周（真实值从货架读）


def week_price():
    try:
        import shop
        v = float(shop.one("week").get("price") or 0)
        return v if v > 0 else PRICE_WEEK
    except Exception:
        return PRICE_WEEK


def card_n():
    """一张周卡给几句（按周清零）"""
    try:
        import shop
        n = int(shop.one("week").get("quota") or 0)
        return n if n > 0 else DAY_QUOTA
    except Exception:
        return DAY_QUOTA
DAY_QUOTA = 20              # 包一周：每天 20 条
IP_DAY_MAX = 20             # 同一 IP 每天最多 20 句
GLOBAL_DAY_MAX = 300        # 全站每天上限，超了自动停
TTS_WARN_CHARS = 8000       # 每天合成字数告警线（约 6.4 元）
TTS_UNIT = 8.0              # 元 / 万字符（复刻音色后付费价）

JOBS = {}
DAY = {}                     # sid -> [日期, 条数]


# ---------------------------------------------------------------- 存储
def _c():
    c = sqlite3.connect(core.DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = _c()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS chat (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sid TEXT, role TEXT, text TEXT, audio TEXT DEFAULT '',
      crisis INTEGER DEFAULT 0, created TEXT);
    CREATE INDEX IF NOT EXISTS ix_chat_sid ON chat(sid, id);
    CREATE TABLE IF NOT EXISTS ent (
      sid TEXT PRIMARY KEY,
      free_used INTEGER DEFAULT 0,
      paid_until TEXT DEFAULT '',
      extra INTEGER DEFAULT 0,
      ip TEXT DEFAULT '',
      note TEXT DEFAULT '',
      created TEXT);
    CREATE TABLE IF NOT EXISTS tts_use (
      d TEXT PRIMARY KEY, chars INTEGER DEFAULT 0, n INTEGER DEFAULT 0);
    """)
    try:
        c.execute("CREATE INDEX IF NOT EXISTS ix_chat_created ON chat(created)")
    except Exception:
        pass
    for col, ddl in (("ip", "TEXT DEFAULT ''"), ("note", "TEXT DEFAULT ''"),
                     ("card_day", "TEXT DEFAULT ''"), ("card_used", "INTEGER DEFAULT 0")):
        try:
            c.execute("ALTER TABLE ent ADD COLUMN %s %s" % (col, ddl))
        except Exception:
            pass
    c.commit()
    c.commit()
    c.close()


def add(sid, role, text, audio="", crisis=0):
    c = _c()
    c.execute("INSERT INTO chat(sid,role,text,audio,crisis,created) VALUES(?,?,?,?,?,?)",
              (sid, role, text, audio, crisis, core.now()))
    c.commit()
    c.close()


def hist(sid, n=8):
    c = _c()
    rows = c.execute("SELECT role,text FROM chat WHERE sid=? ORDER BY id DESC LIMIT ?",
                     (sid, n)).fetchall()
    c.close()
    return [dict(r) for r in reversed(rows)]


def _vk():
    c = sqlite3.connect(core.APP_DB)
    c.row_factory = sqlite3.Row
    d = {r["k"]: r["v"] for r in c.execute("SELECT k,v FROM settings")}
    c.close()
    return d.get("volc_api_key", "")


init_db()


def ent_of(sid, ip=""):
    c = _c()
    r = c.execute("SELECT * FROM ent WHERE sid=?", (sid,)).fetchone()
    if not r:
        c.execute("INSERT OR IGNORE INTO ent(sid,free_used,paid_until,extra,ip,note,created)"
                  " VALUES(?,0,'',0,?,'',?)", (sid, ip, core.now()))
        c.commit()
        r = c.execute("SELECT * FROM ent WHERE sid=?", (sid,)).fetchone()
    elif ip and not (r["ip"] or ""):
        c.execute("UPDATE ent SET ip=? WHERE sid=?", (ip, sid))
        c.commit()
        r = c.execute("SELECT * FROM ent WHERE sid=?", (sid,)).fetchone()
    c.close()
    return dict(r)


def _today():
    return time.strftime("%Y-%m-%d")


def used_today(sid):
    c = _c()
    n = c.execute("SELECT COUNT(*) n FROM chat WHERE sid=? AND role='u' AND created LIKE ?",
                  (sid, _today() + "%")).fetchone()["n"]
    c.close()
    return n


def global_today():
    c = _c()
    n = c.execute("SELECT COUNT(*) n FROM chat WHERE role='u' AND created LIKE ?",
                  (_today() + "%",)).fetchone()["n"]
    c.close()
    return n


def ip_today(ip):
    if not ip:
        return 0
    c = _c()
    n = c.execute("""SELECT COUNT(*) n FROM chat WHERE role='u' AND created LIKE ?
                     AND sid IN (SELECT sid FROM ent WHERE ip=?)""",
                  (_today() + "%", ip)).fetchone()["n"]
    c.close()
    return n


def quota(sid, ip=""):
    e = ent_of(sid, ip)
    pu = (e["paid_until"] or "").strip()
    if pu and pu >= _today():
        used = e["card_used"] or 0
        # 不是今天用的，就从 0 开始算（每天 20 条，隔天自动回满）
        if (e["card_day"] or "").strip() != _today():
            used = 0
        return {"kind": "card", "left": max(0, card_n() - used), "until": pu}
    if (e["extra"] or 0) > 0:
        return {"kind": "extra", "left": e["extra"]}
    return {"kind": "free", "left": max(0, FREE_N - (e["free_used"] or 0))}


def spend(sid, kind):
    c = _c()
    if kind == "free":
        c.execute("UPDATE ent SET free_used=free_used+1 WHERE sid=?", (sid,))
    elif kind == "extra":
        c.execute("UPDATE ent SET extra=MAX(extra-1,0) WHERE sid=?", (sid,))
    elif kind == "card":
        c.execute("UPDATE ent SET card_day=?, card_used=card_used+1 WHERE sid=?",
                  (_today(), sid))
    c.commit()
    c.close()


def grant(sid, days=7):
    import datetime
    e = ent_of(sid)
    base = max(_today(), (e["paid_until"] or _today()))
    try:
        nd = (datetime.date.fromisoformat(base) + datetime.timedelta(days=int(days))).isoformat()
    except Exception:
        nd = _today()
    c = _c()
    c.execute("UPDATE ent SET paid_until=?, card_used=0, card_day='' WHERE sid=?",
              (nd, sid))
    c.commit()
    c.close()
    return nd


BUSY = {"d": ""}


def busy_alert(turns):
    d = _today()
    if BUSY["d"] == d:
        return
    BUSY["d"] = d

    def _m():
        try:
            hp = "/tmp/xin_busy_%s.html" % d
            key = core.get("ops_key")
            with open(hp, "w", encoding="utf-8") as f:
                f.write('<div style="font-family:-apple-system,sans-serif;padding:8px">'
                        '<h2 style="font-size:17px">数字分身今天被说满了</h2>'
                        '<p style="font-size:14px">已经到 %d 轮上限，新的消息现在进不来。</p>'
                        '<p style="font-size:13px;color:#666">要么是被刷了，要么是真火了。'
                        '看一眼运营页里今天的会话数，心里就有数。</p>'
                        '<p style="font-size:13px"><a href="' + conf.u("/xin/chatlog/") + '%s">'
                        '看运营页</a></p></div>' % (turns, key))
            subprocess.run([PY, conf.SENDMAIL, "--to", conf.OPS_EMAIL,
                            "--from-name", conf.MAIL_FROM,
                            "--subject", "数字分身今天说满了（%d 轮）" % turns,
                            "--html", hp],
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
        except Exception:
            pass

    threading.Thread(target=_m, daemon=True).start()


def tts_add(n_chars):
    c = _c()
    c.execute("INSERT INTO tts_use(d,chars,n) VALUES(?,?,1)"
              " ON CONFLICT(d) DO UPDATE SET chars=chars+?, n=n+1",
              (_today(), n_chars, n_chars))
    c.commit()
    c.close()


# ---------------------------------------------------------------- 语气
SAMPLES = """《今晚不劝你坚强》
这个点了，还醒着。
不是睡不着。
是不敢睡。
一躺下，白天的事就一桩一桩回来。
我年轻时候也这样。
后来才明白，天大的事，睡醒了再说。

《一个人也要好好吃饭》
又是一个人吃饭吧。
碗一放，手机一支。
随便扒两口就完事。
我知道。
一个人的饭最难做。
今晚，煮碗面，加个蛋。"""

SYS_CHAT = """{{PERSONA}}

现在你在手机上，跟一个人一条一条语音说话。

规则：

1. 短。两到四句，一句一行。总共 40 到 55 字。超过 55 字就是废话。
2. 像微信语音，不像写信。不要"你好""见字如面""感谢你的信任"。
3. 先接住他那句。用你的话说出他没说的那层。不要复述他的话。
4. 可以反问一句，最多一句，不是每句都问。
5. 不许诺。"会好的""我一直都在""我明天陪你"这类一句都不要。
6. 不讲道理，不列条，不用"首先""其次"。
7. 不用 emoji，不用书名号，不用书面连接词。
8. 不要说"我是AI""我是分身""我尽量回答"，页面已经写清楚了。
9. "我这把年纪了"是口头禅，偶尔用一次，别每句都提。
10. 对方只是打招呼、闲聊，就正常闲聊两句，别硬往深处带。
11. 前面说过的句子不要重复。

他平时说话是这个样子：

%s""" % SAMPLES


def flat(t):
    """把逐行文本压成适合 TTS 读的一整句，行间补逗号做停顿"""
    t = (t or "")
    for ch in "“”‘’《》「」\"":
        t = t.replace(ch, "")
    lines = [x.strip() for x in t.split("\n") if x.strip()]
    s = ""
    for ln in lines:
        if s and s[-1] not in "，。！？、；：,.!?;:":
            s += "，"
        s += ln
    return s


def reply_of(history, text):
    pk = {"u": "对方", "a": "我说的"}
    lines = []
    for m in history[:-1] if history else []:
        if m["role"] in pk:
            lines.append("%s：%s" % (pk[m["role"]], m["text"].replace("\n", " ")))
    prev = "\n".join(lines[-8:]) if lines else "（还没有，这是第一句）"
    user = "前面聊过的：\n%s\n\n对方刚说：%s" % (prev, text)
    out = core.llm(SYS_CHAT.replace("{{PERSONA}}", core.persona()), user, temp=0.92, max_tokens=400)
    out = out.strip().strip('"').strip("“”")
    return out


# ---------------------------------------------------------------- 合成
def _tts(rid, text):
    job = JOBS.get(rid)
    if job is None:
        return
    if not GEN:
        job["status"] = "done"
        return
    try:
        sp = "/tmp/ch_%s.json" % rid
        with open(sp, "w", encoding="utf-8") as f:
            json.dump([{"speaker": VOICE, "text": flat(text)}], f, ensure_ascii=False)
        out = os.path.join(core.MEDIA, "c_%s.mp3" % rid)
        env = dict(os.environ)
        env["VK"] = _vk()
        p = subprocess.run(
            [PY, GEN, "--action", "3", "--script-file", sp,
             "--speakers", VOICE, "--out", out,
             "--head-music", "0", "--tail-music", "0", "--speech-rate", RATE],
            env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=300)
        if p.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 3000:
            try:
                tts_add(len(flat(text)))
            except Exception:
                pass
            job["audio"] = "/xin/m/c_%s.mp3" % rid
            try:
                pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                     "format=duration", "-of", "csv=p=0", out],
                                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=20)
                job["dur"] = round(float((pr.stdout or b"0").decode().strip() or 0), 1)
            except Exception:
                job["dur"] = 0
            job["status"] = "done"
            try:
                c = _c()
                c.execute("UPDATE chat SET audio=? WHERE sid=? AND text=? ORDER BY id DESC LIMIT 1",
                          (job["audio"], job["sid"], job["text"]))
                c.commit()
                c.close()
            except Exception:
                pass
        else:
            job["status"] = "err"
            job["msg"] = (p.stderr or b"").decode("utf-8", "replace")[-200:]
    except Exception as e:
        job["status"] = "err"
        job["msg"] = str(e)[:200]


# ---------------------------------------------------------------- 页面
HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,maximum-scale=1">
<title>老师 · 数字分身</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%}
body{background:#0a0a0a;color:#e8e2d6;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Noto Sans CJK SC",sans-serif;
  -webkit-font-smoothing:antialiased;display:flex;flex-direction:column;height:100vh;height:100dvh;overflow:hidden}
header{flex:0 0 auto;display:flex;align-items:center;gap:11px;padding:13px 16px;padding-top:calc(13px + env(safe-area-inset-top));
  border-bottom:1px solid rgba(201,169,97,.13);background:rgba(10,10,10,.96);backdrop-filter:blur(12px)}
header img{width:40px;height:40px;border-radius:50%;object-fit:cover;border:1px solid rgba(201,169,97,.4)}
.who{flex:1;min-width:0}
.nm{font-size:15px;color:#f2ede2;letter-spacing:.04em;display:flex;align-items:center;gap:7px}
.badge{font-size:9.5px;letter-spacing:.12em;color:#0a0a0a;background:#c9a961;padding:2px 6px;border-radius:2px;font-weight:600}
.st{font-size:10.5px;color:#6d675e;margin-top:3px;letter-spacing:.02em}
.lv{flex:0 0 auto;font-size:11.5px;color:#c9a961;border:1px solid rgba(201,169,97,.35);
  border-radius:3px;padding:5px 9px;text-decoration:none;letter-spacing:.06em}
main{flex:1;overflow-y:auto;padding:20px 15px 8px;-webkit-overflow-scrolling:touch;scroll-behavior:smooth}
main::-webkit-scrollbar{width:0}
.empty{text-align:center;padding:34px 10px 10px}
.hint{font-family:"Songti SC","Noto Serif CJK SC",serif;font-size:16.5px;line-height:2;color:#b9ad95;margin-bottom:26px}
.chips{display:flex;flex-direction:column;gap:9px;max-width:260px;margin:0 auto}
.chips button{background:rgba(255,255,255,.03);border:1px solid rgba(201,169,97,.2);color:#b9ad95;
  font-size:13.5px;padding:11px 14px;border-radius:3px;font-family:inherit;cursor:pointer;transition:.18s}
.chips button:active{background:rgba(201,169,97,.12);color:#e8e2d6}
.row{display:flex;margin-bottom:14px;animation:up .28s ease both}
@keyframes up{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.row.me{justify-content:flex-end}
.bub{max-width:78%;padding:11px 14px;border-radius:4px;font-size:14.5px;line-height:1.75;word-break:break-word}
.me .bub{background:#26231e;color:#ddd6c8;border-top-right-radius:1px}
.him .bub{background:rgba(201,169,97,.075);border:1px solid rgba(201,169,97,.17);color:#e0d9cb;border-top-left-radius:1px;
  max-width:84%;padding:12px 14px 9px}
.him .txt p{margin:0}
.him .txt{font-family:"Songti SC","Noto Serif CJK SC",serif;font-size:15.5px;line-height:1.95;white-space:pre-wrap}
.vbar{display:flex;align-items:center;gap:10px;min-width:186px;margin-top:11px;padding:9px 12px;
  background:rgba(201,169,97,.07);border:1px solid rgba(201,169,97,.16);border-radius:3px;
  cursor:pointer;transition:.2s;-webkit-user-select:none;user-select:none}
.vbar:active{background:rgba(201,169,97,.16)}
.vbar.on{border-color:rgba(201,169,97,.45);background:rgba(201,169,97,.11)}
.vp{font-size:9.5px;color:#c9a961;width:13px;text-align:center;flex:0 0 auto;letter-spacing:0}
.vw{flex:1;height:16px;display:flex;align-items:center;gap:2px;overflow:hidden}
.vw i{display:block;width:2px;flex:0 0 2px;background:rgba(201,169,97,.24);border-radius:1px;transition:background .12s}
.vw i.on{background:#c9a961}
.vs{font-size:11px;color:#8d8578;flex:0 0 auto;letter-spacing:.04em;min-width:26px;text-align:right}
.vbar.pulse{animation:pl 1.6s ease-in-out 3}
@keyframes pl{0%,100%{border-color:rgba(201,169,97,.16)}50%{border-color:rgba(201,169,97,.62)}}
.pay{border:1px solid rgba(201,169,97,.28);background:rgba(201,169,97,.045);border-radius:4px;
  padding:20px 18px 16px;margin:6px 0 16px;text-align:center;animation:up .32s both}
.pay .pt{font-family:"Songti SC","Noto Serif CJK SC",serif;font-size:17px;color:#f2ede2;
  letter-spacing:.05em;margin-bottom:8px}
.pay .pd{font-size:12.5px;color:#9a9286;line-height:1.85;margin-bottom:18px}
.pay .pd b{color:#c9a961;font-weight:600}
.pay img.qr{width:170px;height:170px;object-fit:contain;background:#fff;padding:6px;border-radius:3px;
  display:block;margin:0 auto 9px}
.pay .ph{font-size:11.5px;color:#6d675e;line-height:1.8;margin-bottom:16px}
.pay img.qr2{width:142px;height:142px;object-fit:contain;background:#fff;padding:5px;border-radius:3px;
  display:block;margin:0 auto 8px}
.pay .ps{font-size:12px;color:#9a9286;margin-bottom:11px;letter-spacing:.06em}
.pay .ps:before,.pay .ps:after{content:"";display:inline-block;width:26px;height:1px;
  background:rgba(201,169,97,.28);vertical-align:middle;margin:0 9px}
.pay .pn{font-size:10.5px;color:#4a4640;letter-spacing:.02em;margin-top:6px}
.pay .gobtn{display:block;background:#c9a961;color:#0a0a0a;text-decoration:none;
  border-radius:3px;font-size:14.5px;font-weight:600;padding:12px;letter-spacing:.1em;margin-top:4px}
.rec{display:flex;align-items:center;gap:6px;font-size:11.5px;color:#8d8578;margin-top:8px;letter-spacing:.04em}
.dot{width:4px;height:4px;border-radius:50%;background:#c9a961;animation:bl 1.1s infinite}
.dot:nth-child(2){animation-delay:.18s}.dot:nth-child(3){animation-delay:.36s}
@keyframes bl{0%,60%,100%{opacity:.25}30%{opacity:1}}
.crisis{border:1px solid rgba(220,90,80,.5);background:rgba(220,90,80,.07);border-radius:4px;padding:16px;margin:0 0 16px;animation:up .3s both}
.crisis h4{font-size:14px;color:#e8a49b;margin-bottom:9px;letter-spacing:.03em;font-weight:600}
.crisis p{font-size:13px;color:#b9ad95;line-height:1.95}
.crisis b{color:#e8c9a0;letter-spacing:.06em}
footer{flex:0 0 auto;display:flex;gap:8px;padding:10px 14px;border-top:1px solid rgba(255,255,255,.06);
  background:rgba(10,10,10,.97);padding-bottom:calc(10px + env(safe-area-inset-bottom))}
#in{flex:1;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.08);border-radius:3px;
  color:#e8e2d6;font-family:inherit;font-size:15px;padding:12px 13px;outline:none;transition:.2s}
#in:focus{border-color:rgba(201,169,97,.45);background:rgba(255,255,255,.06)}
#send{background:#c9a961;color:#0a0a0a;border:0;border-radius:3px;font-family:inherit;font-size:14px;
  font-weight:600;padding:0 18px;letter-spacing:.06em;cursor:pointer;transition:.15s}
#send:disabled{opacity:.35}
.tip{flex:0 0 auto;text-align:center;font-size:10px;color:#4a4640;padding:0 0 8px;letter-spacing:.03em;background:#0a0a0a}
</style>
</head>
<body>
<header>
  <img src="/xin/m/avatar-s.png" alt="">
  <div class="who">
    <div class="nm">老师 <span class="badge">数字分身</span></div>
    <div class="st">他本人不在 · 回你的是他的分身</div>
  </div>
  <a class="lv" href="/xin/live">约真人</a>
</header>

<main id="msgs">
  <div class="empty" id="empty">
    <div class="hint">说一句吧。<br>他会回你一段语音。</div>
    <div class="chips">
      <button data-t="我睡不着，一躺下就想事">我睡不着，一躺下就想事</button>
      <button data-t="跟家里人吵了一架，心里堵得慌">跟家里人吵了一架</button>
      <button data-t="最近干什么都提不起劲">最近干什么都提不起劲</button>
    </div>
  </div>
</main>

<footer>
  <input id="in" placeholder="说一句…" maxlength="300" autocomplete="off">
  <button id="send">发</button>
</footer>
<div class="tip">AI 语音合成 · 声音经本人授权 · 非本人实时回复</div>

<script>
var SID = localStorage.getItem('xchsid') || '';
var BUSY = false;
var MAIN = document.getElementById('msgs');
var IN = document.getElementById('in');
var BTN = document.getElementById('send');
var EMPTY = document.getElementById('empty');

function toBottom(){
  setTimeout(function(){ MAIN.scrollTop = MAIN.scrollHeight; }, 60);
}

function addMe(t){
  if (EMPTY) { EMPTY.remove(); EMPTY = null; }
  var d = document.createElement('div');
  d.className = 'row me';
  var b = document.createElement('div');
  b.className = 'bub'; b.textContent = t;
  d.appendChild(b); MAIN.appendChild(d); toBottom();
}

function addHim(t){
  if (EMPTY) { EMPTY.remove(); EMPTY = null; }
  var d = document.createElement('div');
  d.className = 'row him';
  var b = document.createElement('div');
  b.className = 'bub';
  var x = document.createElement('div');
  x.className = 'txt'; x.textContent = t;
  var r = document.createElement('div');
  r.className = 'rec';
  r.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span><span>正在录…</span>';
  b.appendChild(x); b.appendChild(r);
  d.appendChild(b); MAIN.appendChild(d); toBottom();
  return d;
}

function makeVoice(bub, url, dur){
  var r = bub.querySelector('.rec');
  if (r) r.remove();
  var hs = [], i;
  for (i = 0; i < 26; i++) { hs.push(3 + Math.round(Math.abs(Math.sin(i * 1.73 + 0.6)) * 10)); }
  var el = document.createElement('div');
  el.className = 'vbar';
  var html = '<span class="vp">&#9654;</span><span class="vw">';
  for (i = 0; i < hs.length; i++) { html += '<i style="height:' + hs[i] + 'px"></i>'; }
  html += '</span><span class="vs">' + (dur ? Math.round(dur) + '&Prime;' : '\u8bed\u97f3') + '</span>';
  el.innerHTML = html;
  bub.appendChild(el);
  toBottom();

  var au = new Audio(url);
  au.preload = 'auto';
  var bars = el.querySelectorAll('.vw i');
  var on = false;
  el.onclick = function(){
    if (on) { au.pause(); } else { au.play().catch(function(){}); }
  };
  au.onplay = function(){ on = true; el.classList.add('on'); el.querySelector('.vp').innerHTML = '&#10074;&#10074;'; };
  au.onpause = function(){ on = false; el.classList.remove('on'); el.querySelector('.vp').innerHTML = '&#9654;'; };
  au.onended = function(){
    on = false; el.classList.remove('on'); el.querySelector('.vp').innerHTML = '&#9654;';
    for (var k = 0; k < bars.length; k++) bars[k].className = '';
  };
  au.ontimeupdate = function(){
    var p = au.duration ? au.currentTime / au.duration : 0;
    var n = Math.round(p * bars.length);
    for (var k = 0; k < bars.length; k++) bars[k].className = (k < n ? 'on' : '');
  };
  setTimeout(function(){ el.classList.add('pulse'); }, 120);
  setTimeout(function(){ el.classList.remove('pulse'); }, 5800);
  return el;
}

function addPay(kind){
  if (EMPTY) { EMPTY.remove(); EMPTY = null; }
  var d = document.createElement('div');
  d.className = 'pay';
  var head = (kind === 'card') ? '今天这五句，说完了' : '先聊到这儿';
  var pd = (kind === 'balance')
    ? '余额不够了。<br>充 <b>30</b> 元，还能说 30 句。'
    : '想接着说 —— 充 <b>30</b> 元，说 30 句。<br>想让他亲手回信 —— 99。';
  d.innerHTML =
    '<div class="pt">' + head + '</div>' +
    '<div class="pd">' + pd + '</div>' +
    '<a class="gobtn" href="/xin/me">去充值</a>' +
    '<div class="ph" style="margin-top:13px">钱直接到他账上，不经过任何人</div>';
  MAIN.appendChild(d); toBottom();
}

function setLeft(n){
  if (n === null || n === undefined) return;
  n = parseInt(n, 10);
  if (isNaN(n)) return;
  IN.placeholder = (n > 0) ? ('还能说 ' + n + ' 句…') : '今天说到这儿了';
}

function addCrisis(t){
  if (EMPTY) { EMPTY.remove(); EMPTY = null; }
  var d = document.createElement('div');
  d.className = 'crisis';
  d.innerHTML = '<h4>这句，他没让分身接</h4>' +
    '<p>' + t + '<br><br>这条已经留给他本人。<br>' +
    '如果此刻很难受，请打 <b>400-161-9995</b>（希望24热线，24小时都有人）。<br>' +
    '或者打 <b>010-8295-1332</b>（北京心理危机研究与干预中心）。</p>';
  MAIN.appendChild(d); toBottom();
}

function poll(rid, d){
  var n = 0;
  var t = setInterval(function(){
    n++;
    if (n > 60) { clearInterval(t); return; }
    fetch('api/chat/' + rid).then(function(r){ return r.json(); }).then(function(j){
      if (j.status === 'done') {
        clearInterval(t);
        makeVoice(d.querySelector('.bub'), j.audio, j.dur);
      } else if (j.status === 'err') {
        clearInterval(t);
        var r = d.querySelector('.rec');
        if (r) r.innerHTML = '<span>这段没录上，再发一句试试</span>';
      }
    }).catch(function(){});
  }, 1500);
}

function say(text){
  text = (text || '').trim();
  if (!text || BUSY) return;
  BUSY = true; BTN.disabled = true; IN.value = '';
  addMe(text);
  fetch('api/chat/say', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({sid: SID, text: text})
  }).then(function(r){ return r.json(); }).then(function(j){
    BUSY = false; BTN.disabled = false;
    if (j.sid) { SID = j.sid; localStorage.setItem('xchsid', SID); }
    if (j.crisis) {
      addCrisis('你写的这些话，已经不是随便聊两句能接住的了。');
      return;
    }
    if (j.pay) {
      addPay(j.kind);
      setLeft(0);
      return;
    }
    if (!j.ok) {
      addHim(j.msg || '刚才没听清。你再说一句。');
      return;
    }
    setLeft(j.left);
    var d = addHim(j.reply);
    poll(j.rid, d);
  }).catch(function(){
    BUSY = false; BTN.disabled = false;
    addHim('这边有点卡。再发一次？');
  });
}

BTN.onclick = function(){ say(IN.value); };
IN.addEventListener('keydown', function(e){ if (e.key === 'Enter') say(IN.value); });
document.querySelectorAll('.chips button').forEach(function(b){
  b.onclick = function(){ say(b.dataset.t); };
});
window.addEventListener('load', function(){
  fetch('api/chat/quota?sid=' + encodeURIComponent(SID)).then(function(r){ return r.json(); })
    .then(function(j){ if (j && j.left !== undefined) setLeft(j.left); }).catch(function(){});
  if (SID) {
    fetch('api/chat/hist?sid=' + encodeURIComponent(SID)).then(function(r){ return r.json(); })
    .then(function(j){
      if (!j.items || !j.items.length) return;
      if (EMPTY) { EMPTY.remove(); EMPTY = null; }
      j.items.forEach(function(m){
        if (m.role === 'u') addMe(m.text);
        else {
          var d = addHim(m.text);
          if (m.audio) makeVoice(d.querySelector('.bub'), m.audio, 0);
          else { var r = d.querySelector('.rec'); if (r) r.remove(); }
        }
      });
    }).catch(function(){});
  }
});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------- 路由
def install(app):
    from fastapi import Request
    from fastapi.responses import HTMLResponse, JSONResponse

    @app.get("/xin/chat", response_class=HTMLResponse)
    def _chat_page():
        return HTML

    @app.post("/xin/api/chat/say")
    async def _chat_say(req: Request):
        d = await req.json()
        text = (d.get("text") or "").strip()[:600]
        sid = (d.get("sid") or "").strip()[:40]
        ip = ""
        try:
            ip = req.client.host or ""
        except Exception:
            pass
        if not text:
            return {"ok": 0, "msg": "空的"}
        if not sid:
            sid = core.new_token(10)

        # 危机词：不扣额度、不受限流，永远回
        if core.crisis_hit(text):
            add(sid, "u", text)
            add(sid, "c", "|".join(core.crisis_hit(text)), crisis=1)
            return {"ok": 1, "sid": sid, "crisis": 1}

        # 闸三：全站日限
        if global_today() >= GLOBAL_DAY_MAX:
            busy_alert(GLOBAL_DAY_MAX)
            return {"ok": 0, "sid": sid, "busy": 1,
                    "msg": "今天说的人太多，他先歇了。明天再来。"}
        # 闸二：同 IP
        if ip and ip_today(ip) >= IP_DAY_MAX:
            return {"ok": 0, "sid": sid, "msg": "今天说得有点多了，明天再来吧"}
        # 已登录：走余额
        uid = 0
        try:
            uid = _acct.uid_of(req)
        except Exception:
            uid = 0
        u = _acct.me(uid) if uid else None
        if not u:
            uid = 0

        if uid:
            bal = round(u["balance"] or 0, 2)
            if bal < _acct.CHAT_PRICE:
                return {"ok": 0, "sid": sid, "pay": 1, "kind": "balance",
                        "balance": bal, "price": _acct.CHAT_PRICE}
            okc, nb = _acct.charge(uid, _acct.CHAT_PRICE, "chat", "")
            if not okc:
                return {"ok": 0, "sid": sid, "pay": 1, "kind": "balance", "balance": nb}
            qkind = "balance"
            left_after = int(nb // _acct.CHAT_PRICE)
        else:
            q = quota(sid, ip)
            if q["left"] <= 0:
                return {"ok": 0, "sid": sid, "pay": 1, "kind": q["kind"],
                        "price": week_price(), "until": q.get("until", "")}
            qkind = q["kind"]
            left_after = q["left"]

        add(sid, "u", text)
        try:
            rp = reply_of(hist(sid, 9), text)
        except Exception as e:
            return {"ok": 0, "sid": sid, "msg": "模型没应答：%s" % str(e)[:60]}
        if not rp:
            return {"ok": 0, "sid": sid, "msg": "空回复"}
        add(sid, "a", rp)
        if qkind != "balance":
            spend(sid, qkind)
            left_after = quota(sid, ip)["left"]

        rid = core.new_token(10)
        JOBS[rid] = {"status": "tts", "text": rp, "sid": sid, "audio": "", "ts": time.time()}
        threading.Thread(target=_tts, args=(rid, rp), daemon=True).start()
        return {"ok": 1, "sid": sid, "rid": rid, "reply": rp,
                "left": left_after, "kind": qkind, "uid": uid}

    @app.get("/xin/api/chat/hist")
    def _chat_hist(sid: str = ""):
        if not sid:
            return {"items": []}
        c = _c()
        rows = c.execute("SELECT role,text,audio,crisis FROM chat WHERE sid=? AND crisis=0 ORDER BY id LIMIT 100",
                         (sid,)).fetchall()
        c.close()
        return {"items": [dict(r) for r in rows if r["role"] in ("u", "a")]}

    @app.get("/xin/api/chat/quota")
    def _chat_quota(sid: str = ""):
        if not sid:
            return {"kind": "free", "left": FREE_N, "price": week_price()}
        q = quota(sid)
        q["price"] = week_price()
        return q

    @app.post("/xin/api/chat/grant")
    async def _chat_grant(req: Request):
        d = await req.json()
        if (d.get("key") or "") != core.get("ops_key"):
            return {"ok": 0, "msg": "没有权限"}
        sid = (d.get("sid") or "").strip()
        days = int(d.get("days") or 7)
        if not sid:
            return {"ok": 0, "msg": "缺 sid"}
        nd = grant(sid, days)
        return {"ok": 1, "until": nd}

    @app.get("/xin/api/chat/{rid}")
    def _chat_poll(rid: str):
        j = JOBS.get(rid)
        if not j:
            return {"status": "err", "msg": "没有这一条"}
        return {"status": j["status"], "audio": j.get("audio", ""), "dur": j.get("dur", 0)}

    @app.get("/xin/chatlog/{key}", response_class=HTMLResponse)
    def _chat_log(key: str):
        if not key or key != core.get("ops_key"):
            return HTMLResponse("<h2>没有入口</h2>", status_code=403)
        c = _c()
        rows = c.execute("""SELECT sid, MIN(created) t0, MAX(created) t1, COUNT(*) n,
                  (SELECT text FROM chat WHERE sid=c.sid AND role='u' ORDER BY id LIMIT 1) first
                  FROM chat c WHERE crisis=0 GROUP BY sid ORDER BY t1 DESC LIMIT 100""").fetchall()
        crisis = c.execute("SELECT sid,text,created FROM chat WHERE crisis=1 ORDER BY id DESC LIMIT 20").fetchall()
        u = c.execute("SELECT chars,n FROM tts_use WHERE d=?", (_today(),)).fetchone()
        c.close()
        uc = (u["chars"] if u else 0) or 0
        un = (u["n"] if u else 0) or 0
        cost = uc / 10000.0 * 8.0

        h = ['<!DOCTYPE html><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>夜话 · 运营</title><style>',
             'body{background:#0a0a0a;color:#ddd6c8;font-family:-apple-system,"PingFang SC",sans-serif;',
             'padding:16px 14px 40px;line-height:1.7;font-size:14px;margin:0}',
             'a{color:#c9a961;text-decoration:none}',
             'h1{font-size:19px;color:#f2ede2;letter-spacing:.08em;margin:6px 0 16px;font-weight:600}',
             'h2{font-size:14px;color:#c9a961;margin:26px 0 10px;letter-spacing:.06em;font-weight:500}',
             '.top{background:rgba(201,169,97,.06);border:1px solid rgba(201,169,97,.2);border-radius:4px;',
             'padding:13px 15px;font-size:13px;color:#b9ad95;margin-bottom:8px}',
             '.top b{color:#f2ede2;font-size:16px}',
             '.i{border-left:2px solid rgba(201,169,97,.55);padding:9px 0 9px 12px;margin-bottom:11px}',
             '.l1{font-size:14px;margin-bottom:3px}',
             '.t{font-size:11.5px;color:#6d675e}',
             '.x{color:#e8a49b}',
             'button{background:rgba(201,169,97,.14);border:1px solid rgba(201,169,97,.4);color:#c9a961;',
             'font-family:inherit;font-size:11.5px;padding:4px 11px;border-radius:3px;margin-top:6px;cursor:pointer}',
             'button:active{background:rgba(201,169,97,.3)}',
             '.ok{color:#8fd39c}',
             '</style>',
             '<div style="display:flex;align-items:center;gap:11px;margin:0 0 18px"><img src="/xin/m/avatar-s.png" alt="" style="width:42px;height:42px;border-radius:21px;object-fit:cover;border:1px solid rgba(201,169,97,.4)"><div style="font-size:12.5px;color:#A79C89;letter-spacing:.1em">我的小站</div></div>',
             '<h1>夜话 · 数字分身</h1>',
             '<div class="top">今天 <b>%d</b> 轮　%d 段语音　<b>%d</b> 字　约 <b>%.1f</b> 元'
             '<br><span class="t">全站日限 %d 轮 · 合成 %.0f 元/万字符</span></div>'
             % (global_today(), un, uc, cost, GLOBAL_DAY_MAX, TTS_UNIT)]

        if crisis:
            h.append('<h2>需要你看一眼（%d）</h2>' % len(crisis))
            for r in crisis:
                h.append('<div class="i"><div class="t">%s</div><div class="x">%s</div>'
                         '<div class="t"><a href="/xin/chatlog/%s/%s">看这段对话</a></div></div>'
                         % (r["created"], r["text"], key, r["sid"]))

        h.append('<h2>最近的对话（%d）</h2>' % len(rows))
        for r in rows:
            q = quota(r["sid"])
            if q["kind"] == "card":
                st = '<span class="ok">周卡至 %s · 今日还剩 %d 句</span>' % (
                    (q.get("until") or "")[5:], q["left"])
            elif q["kind"] == "extra":
                st = '单条 · 剩 %d' % q["left"]
            else:
                st = '免费 · 剩 %d 句' % q["left"]
            first = (r["first"] or "").replace("\n", " ")[:34]
            h.append(
                '<div class="i"><div class="l1"><a href="/xin/chatlog/%s/%s">%s</a></div>'
                '<div class="t">%s · %d 条 · %s</div>'
                '<div class="t">%s</div>'
                '<button onclick="gr(this,\'%s\')">开 7 天</button></div>'
                % (key, r["sid"], first or ("会话 " + r["sid"][:6]),
                   r["t1"][5:16], r["n"], st, r["t0"][5:16], r["sid"]))

        h.append('<script>function gr(b,sid){var d=prompt("开通几天？","7");if(!d)return;'
                 'fetch("/xin/api/chat/grant",{method:"POST",headers:{"Content-Type":"application/json"},'
                 'body:JSON.stringify({key:"%s",sid:sid,days:parseInt(d)})}).then(function(r){return r.json();})'
                 '.then(function(j){if(j.ok){b.textContent="已开到 "+j.until;b.style.color="#8fd39c";}'
                 'else{b.textContent=j.msg||"失败";}}).catch(function(){b.textContent="网络失败";});}'
                 '</script>' % key)
        return "".join(h)

    @app.get("/xin/chatlog/{key}/{sid}", response_class=HTMLResponse)
    def _chat_one(key: str, sid: str):
        if not key or key != core.get("ops_key"):
            return HTMLResponse("<h2>没有入口</h2>", status_code=403)
        c = _c()
        rows = c.execute("SELECT role,text,audio,created FROM chat WHERE sid=? ORDER BY id",
                         (sid,)).fetchall()
        e = c.execute("SELECT * FROM ent WHERE sid=?", (sid,)).fetchone()
        c.close()
        q = quota(sid)
        h = ['<!DOCTYPE html><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             '<style>body{background:#0a0a0a;color:#ddd6c8;font-family:-apple-system,"PingFang SC",sans-serif;',
             'padding:16px 14px 40px;font-size:14.5px;line-height:1.9;margin:0}',
             'a{color:#c9a961;text-decoration:none}',
             '.m{margin-bottom:14px;padding:10px 13px;border-radius:4px;white-space:pre-wrap}',
             '.u{background:#26231e;margin-left:20%}',
             '.a{background:rgba(201,169,97,.07);border:1px solid rgba(201,169,97,.16);margin-right:12%}',
             '.c{background:rgba(220,90,80,.1);border:1px solid rgba(220,90,80,.4);color:#e8a49b}',
             '.t{font-size:11px;color:#6d675e;margin-bottom:5px}',
             'audio{width:100%;height:28px;margin-top:6px;filter:invert(.9) hue-rotate(180deg) saturate(.4)}',
             '</style>',
             '<a href="/xin/chatlog/%s">← 回到列表</a>' % key]
        if e:
            h.append('<div class="t" style="margin-top:10px">免费已用 %s 句 · 周卡到 %s · 单条余 %s · %s</div>'
                     % (e["free_used"], e["paid_until"] or "—", e["extra"], q["kind"]))
        for r in rows:
            if r["role"] == "u":
                cls, nm = "u", "对方"
            elif r["role"] == "c":
                cls, nm = "c", "熔断"
            else:
                cls, nm = "a", "分身"
            au = '<audio controls src="%s"></audio>' % r["audio"] if r["audio"] else ""
            h.append('<div class="m %s"><div class="t">%s · %s</div>%s%s</div>'
                     % (cls, nm, r["created"][5:16], r["text"], au))
        return "".join(h)
