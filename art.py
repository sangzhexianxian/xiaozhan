# -*- coding: utf-8 -*-
"""画廊（2026-11-16）

- 粉丝端 /xin/art   ：分卷陈列，标价，可点开看大图
- 后台   /xin/artops/{key}：改价、标已售、上下架
数据存 settings.art_works（JSON），缺失项用下面的 DEF 兜底。
图片放在 media/art/ 下，经 /xin/m/art/ 对外提供（P1.jpg、P2.jpg…）。
"""
import html as H
import json
import time

import core
import conf

BASE = conf.u("/xin/m/art")

# id, 名称, 卷, 默认价  —— 换成你自己的作品即可
DEF = [
    ("p01", "示例作品一", "第一卷", 680),
    ("p02", "示例作品二", "第一卷", 880),
    ("p03", "示例作品三", "第二卷", 1280),
]

VOLS = [
    ("第一卷", "这一卷可以写一句你自己的话", ""),
    ("第二卷", "", ""),
]

NOTE = {}


def works():
    """返回 {id: {...}}，以后台设置为准，缺的用 DEF"""
    raw = core.get("art_works") or ""
    saved = {}
    try:
        for x in json.loads(raw):
            if x.get("id"):
                saved[x["id"]] = x
    except Exception:
        pass
    out = {}
    for pid, name, vol, price in DEF:
        s = saved.get(pid) or {}
        out[pid] = {
            "id": pid,
            "t": name,
            "g": vol,
            "price": float(s.get("price", price) or 0),
            "on": int(s.get("on", 1)),
            "sold": int(s.get("sold", 0)),
        }
    return out


def money(v):
    v = float(v or 0)
    return ("%d" % v) if abs(v - round(v)) < 0.01 else ("%.2f" % v)


def thumb(pid):
    return BASE + "/t/" + pid + ".jpg"


def big(pid):
    return BASE + "/b/" + pid + ".jpg"


CSS = """
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:#0B0A08;color:#F2ECDF;
 font-family:"Songti SC","Noto Serif CJK SC","Source Han Serif SC",Georgia,serif;
 font-size:16.5px;line-height:1.9;letter-spacing:.02em;
 padding:calc(34px + env(safe-area-inset-top)) 22px calc(70px + env(safe-area-inset-bottom));
 max-width:620px;margin:0 auto;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.hd{display:flex;align-items:center;gap:13px;margin-bottom:40px}
.hd img{width:44px;height:44px;border-radius:22px;object-fit:cover;
 border:1px solid rgba(201,169,97,.4)}
.hd .nm{font-size:15px;color:#A79E8B;letter-spacing:.16em;line-height:1.5}
.hd .nm small{display:block;font-size:11.5px;color:#7C7568;letter-spacing:.4em;margin-top:3px}
.title{text-align:center;margin:0 0 10px}
.title h1{font-size:30px;letter-spacing:.5em;color:#F7F2E6;font-weight:600;
 padding-left:.5em}
.title .sb{font-size:13px;color:#A87F4A;letter-spacing:.3em;margin-top:14px}
.title .ln{width:52px;height:1px;background:rgba(201,169,97,.45);margin:22px auto 0}

.vol{text-align:center;margin:56px 0 22px}
.vol .no{font-size:12px;color:#6B6355;letter-spacing:.4em}
.vol h2{font-size:23px;letter-spacing:.42em;color:#F2ECDF;font-weight:600;
 margin-top:10px;padding-left:.42em}
.vol .vs{font-size:13.5px;color:#8F8776;letter-spacing:.12em;margin-top:10px}

.gal{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.w{display:block;border:1px solid rgba(201,169,97,.16);border-radius:3px;
 overflow:hidden;background:#11100C}
.w img{display:block;width:100%;aspect-ratio:68/100;object-fit:cover}
.w .cap{padding:13px 13px 15px}
.w .cap b{display:block;font-size:16.5px;color:#F2ECDF;font-weight:400;
 letter-spacing:.12em}
.w .cap .pr{display:block;font-size:15px;color:#E6CD91;margin-top:6px;letter-spacing:.04em}
.w .cap .pr i{font-style:normal;font-size:12.5px;color:#7C7568;margin-left:6px}
.w.off{opacity:.4}
.w.off .cap .pr{color:#8F8776}
.w.full{grid-column:1 / -1}
.w.full img{aspect-ratio:auto}
.w.full .cap{padding:17px 18px 19px}
.w.full .cap b{font-size:20px;letter-spacing:.2em}
.w.full .cap .pr{font-size:18px;margin-top:8px}
.w.full .cap .st{font-size:14px;color:#8F8776;line-height:1.85;margin-top:9px}

.colo{display:flex;align-items:center;justify-content:center;gap:16px;
 margin:46px 0 0;font-size:14px;color:#A87F4A;letter-spacing:.34em}
.colo i{width:36px;height:1px;background:rgba(201,169,97,.28)}

.how{margin:64px 0 0;border-top:1px solid rgba(201,169,97,.18);padding-top:32px}
.how .sh{font-size:13.5px;color:#A87F4A;letter-spacing:.32em;margin-bottom:6px}
.how .rule{height:1px;margin:0 0 22px;
 background:linear-gradient(90deg,rgba(201,169,97,.45),rgba(201,169,97,.03))}
.how p{font-size:15.5px;color:#A79E8B;line-height:2.15;margin-bottom:12px}
.how p b{color:#E6CD91;font-weight:400}

.foot{text-align:center;font-size:13.5px;color:#6B6355;margin-top:52px;line-height:2.2}
.foot a{color:#8D6C42}

.lb{position:fixed;inset:0;background:rgba(6,5,4,.98);z-index:99;display:none;
 padding:52px 20px 30px;overflow-y:auto;-webkit-overflow-scrolling:touch}
.lb.on{display:block}
.lb .x{position:fixed;top:10px;right:16px;font-size:26px;color:#A79E8B;
 padding:10px 14px;line-height:1;z-index:2}
.lb img#lbi{display:block;width:auto;max-width:100%;max-height:21vh;margin:0 auto;
 border:1px solid rgba(201,169,97,.2)}
.lb .c{text-align:center;margin:12px auto 0;max-width:460px}
.lb .c b{display:block;font-size:20px;letter-spacing:.22em;color:#F7F2E6;font-weight:600}
.lb .c .p{font-size:17px;color:#E6CD91;margin-top:5px}
.lb .c .s{font-size:13px;color:#8F8776;margin-top:7px;line-height:1.75}
.lb .c .b{margin-top:14px;display:inline-block;padding:13px 32px;
 border:1px solid rgba(201,169,97,.55);color:#E6CD91;font-size:16px;letter-spacing:.16em;
 background:transparent;font-family:inherit;cursor:pointer}
.lb .who{display:flex;gap:9px;margin-top:13px}
.lb .who input{flex:1;min-width:0;padding:12px 13px;font-size:14px;
 background:rgba(255,255,255,.05);border:1px solid rgba(201,169,97,.26);
 color:#F2ECDF;font-family:inherit;border-radius:3px}
.lb .who input::placeholder{color:#6B6355}
.lb .steps{font-size:12.5px;color:#A79E8B;line-height:1.75;margin-top:10px;
 text-align:left;background:rgba(201,169,97,.055);border:1px solid rgba(201,169,97,.16);
 border-radius:3px;padding:10px 12px}
.lb .steps b{color:#C9A961;font-weight:400;margin-right:4px}
.lb .qr{display:block;width:132px;height:132px;margin:10px auto 0;
 border:1px solid rgba(201,169,97,.25);border-radius:3px}
.lb .hint{font-size:12.5px;color:#7C7568;line-height:1.8;margin-top:9px}
"""

JS = """
var CUR='';
function op(i){
  var d=document.getElementById('d'+i), lb=document.getElementById('lb');
  CUR=i;
  document.getElementById('lbi').src=d.dataset.big;
  document.getElementById('lbt').textContent=d.dataset.t;
  document.getElementById('lbp').textContent=d.dataset.p2;
  document.getElementById('lbs').textContent=d.dataset.s||'';
  document.getElementById('lbpay').style.display=d.dataset.sold==='1'?'none':'block';
  document.getElementById('lbdone').style.display='none';
  document.getElementById('lbb').style.display='inline-block';
  lb.classList.add('on');
}
function cl(){document.getElementById('lb').classList.remove('on')}
function paid(){
  var b=document.getElementById('lbb');
  b.disabled=true; b.textContent='正在告诉他…';
  fetch('/xin/api/art/pay',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({art:CUR,
      who:(document.getElementById('lbwho')||{}).value||'',
      contact:(document.getElementById('lbcx')||{}).value||'',
      note:''})})
  .then(function(r){return r.json()}).then(function(j){
    if(j.ok){
      b.style.display='none';
      var d=document.getElementById('lbdone');
      d.style.display='block';
      d.textContent='好，已经告诉他了。他会先看一眼，然后联系你。';
    }else{
      b.disabled=false; b.textContent='再 试 一 次';
    }
  }).catch(function(){b.disabled=false;b.textContent='再 试 一 次'});
}
"""


def page(req=None):
    w = works()
    h = ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
         '<title>画 · 我的小站</title><style>' + CSS + '</style></head><body>']

    h.append('<div class="hd"><img src="/xin/m/avatar-s.png" alt="">'
             '<div class="nm">老师<small>画</small></div></div>')

    h.append('<div class="title"><h1>画</h1>'
             '<div class="sb">原作 · 限量</div>'
             '<div class="ln"></div></div>')

    for vi, (vol, sub, colo) in enumerate(VOLS):
        items = [w[p[0]] for p in DEF if p[2] == vol and w[p[0]]["on"]]
        if not items:
            continue
        h.append('<div class="vol"><div class="no">卷 ' + "一二三"[vi] + '</div>'
                 '<h2>' + H.escape(vol) + '</h2>'
                 '<div class="vs">' + H.escape(sub) + '</div></div>')
        h.append('<div class="gal">')
        for it in items:
            pid = it["id"]
            sold = it["sold"]
            cls = "w" + (" off" if sold else "")
            if pid == "p11":
                cls += " full"
            price = ("已 售" if sold else "¥" + money(it["price"]))
            note = NOTE.get(pid, "")
            h.append('<a class="' + cls + '" id="d' + pid + '" href="javascript:op(\'' + pid + '\')"'
                     ' data-big="' + big(pid) + '" data-t="' + H.escape(it["t"]) + '"'
                     ' data-p2="' + price + '" data-sold="' + str(sold) + '"'
                     ' data-s="' + H.escape(note) + '"'
                     ' data-href="/xin/liuyan?art=' + pid + '">'
                     '<img loading="lazy" src="' + thumb(pid) + '" alt="' + H.escape(it["t"]) + '">'
                     '<div class="cap"><b>' + H.escape(it["t"]) + '</b>'
                     '<span class="pr">' + price + '<i>原作</i></span>')
            if pid == "p11" and note:
                h.append('<div class="st">' + H.escape(note) + '</div>')
            h.append('</div></a>')
        h.append('</div>')
        if colo:
            h.append('<div class="colo"><i></i><span>' + H.escape(colo) + '</span><i></i></div>')

    h.append('<div class="how"><div class="sh">怎 么 请 一 幅</div>'
             '<div class="rule"></div>'
             '<p><b>每一幅都是原件。</b>不是复制品，不是印刷。</p>'
             '<p>喜欢哪一幅，点开，按「我想要这幅」，把你的想法写给他。'
             '他会亲自跟你聊——尺寸、装裱、怎么寄，都当面说清。</p>'
             '<p>钱不在这里付。<b>谈妥了再说。</b></p></div>')

    h.append('<div class="foot">画 与 声，都是他一个人的<br>'
             '<a href="/xin/">← 回门厅</a></div>')

    h.append('<div class="lb" id="lb"><span class="x" onclick="cl()">×</span>'
             '<img id="lbi" alt=""><div class="c"><b id="lbt"></b>'
             '<div class="p" id="lbp"></div><div class="s" id="lbs"></div>'
             '<div id="lbpay">'
             '<div class="who">'
             '<input id="lbwho" maxlength="16" placeholder="怎么称呼你">'
             '<input id="lbcx" maxlength="40" placeholder="微信或手机（方便我联系你）">'
             '</div>'
             '<div class="steps">'
             '<b>①</b> 长按下面这张图，选「保存图片」<br>'
             '<b>②</b> 微信 → 扫一扫 → 右上角「相册」→ 选它<br>'
             '<b>③</b> 付完，点下面这个按钮'
             '</div>'
             '<img class="qr" id="lbqr" src="/xin/m/pay.png?v=2" alt="">'
             '<button class="b" id="lbb" onclick="paid()">我 已 经 付 好 了</button>'
             '<div class="hint">点完他会收到 · 这幅先给你留着</div></div>'
             '<div id="lbdone" style="display:none;font-size:16px;color:#8FD3AE;'
             'margin-top:22px;line-height:2"></div></div></div>')

    h.append('<script>' + JS + '</script></body></html>')
    return "".join(h)


# ============================== 后台 ==============================
OPS_CSS = """
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:#0B0A08;color:#F2ECDF;
 font-family:"Songti SC","Noto Serif CJK SC",Georgia,serif;
 font-size:17px;line-height:1.9;
 padding:calc(32px + env(safe-area-inset-top)) 20px calc(60px + env(safe-area-inset-bottom));
 max-width:600px;margin:0 auto}
a{color:inherit;text-decoration:none}
.hd{display:flex;align-items:center;gap:12px;margin-bottom:30px}
.hd img{width:42px;height:42px;border-radius:21px;border:1px solid rgba(201,169,97,.4)}
.hd .nm{font-size:19px;letter-spacing:.24em;color:#F7F2E6}
.hd .nm small{display:block;font-size:12px;color:#A87F4A;letter-spacing:.4em;margin-top:4px}
.vh{font-size:14px;color:#A87F4A;letter-spacing:.34em;margin:34px 0 4px}
.rule{height:1px;background:linear-gradient(90deg,rgba(201,169,97,.45),rgba(201,169,97,.03));
 margin:0 0 16px}
.r{display:flex;align-items:center;gap:14px;padding:16px 0;
 border-bottom:1px solid rgba(201,169,97,.1)}
.r img{width:56px;height:82px;object-fit:cover;border:1px solid rgba(201,169,97,.2);flex:0 0 auto}
.r .m{flex:1;min-width:0}
.r .m b{display:block;font-size:18px;color:#F2ECDF;font-weight:400;letter-spacing:.1em}
.r .m .sw{margin-top:9px;display:flex;gap:9px}
.r .m .sw button{border:1px solid rgba(201,169,97,.32);background:transparent;
 color:#8F8776;font-family:inherit;font-size:14px;padding:6px 13px;border-radius:3px}
.r .m .sw button.on{border-color:rgba(201,169,97,.6);color:#E6CD91;
 background:rgba(201,169,97,.1)}
.r .m .sw button.sd.on{border-color:rgba(200,120,90,.6);color:#D89A80;
 background:rgba(200,120,90,.1)}
.r .pr{flex:0 0 auto;text-align:right}
.r .pr input{width:96px;padding:11px 8px;text-align:right;font-size:18px;
 background:rgba(255,255,255,.05);border:1px solid rgba(201,169,97,.3);
 color:#E6CD91;font-family:inherit;border-radius:3px}
.r .pr label{display:block;font-size:12px;color:#6B6355;margin-top:5px}
.save{width:100%;margin-top:34px;padding:22px;border:1px solid rgba(201,169,97,.55);
 background:transparent;color:#E6CD91;font-family:inherit;font-size:19px;
 letter-spacing:.3em;border-radius:3px}
.ok{position:fixed;left:0;right:0;bottom:0;padding:18px;text-align:center;
 background:#1C4A36;color:#EAF6EF;font-size:17px;transform:translateY(100%);
 transition:.25s}
.ok.on{transform:translateY(0)}
.back{display:block;margin-top:30px;text-align:center;font-size:15px;color:#8D6C42}
"""

OPS_JS = """
function tg(el,cls){el.classList.toggle(cls)}
function sv(){
  var out=[];
  document.querySelectorAll('.r').forEach(function(r){
    var b=r.querySelectorAll('.sw button');
    out.push({id:r.dataset.id,
      price:parseFloat(r.querySelector('input').value)||0,
      on:b[0].classList.contains('on')?1:0,
      sold:b[1].classList.contains('on')?1:0});
  });
  var btn=document.querySelector('.save'); btn.textContent='正在存…'; btn.disabled=true;
  fetch('/xin/api/art/save',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({key:document.body.dataset.k,items:out})})
  .then(function(r){return r.json()}).then(function(j){
    btn.textContent='保 存'; btn.disabled=false;
    if(j.ok){var o=document.getElementById('ok');o.classList.add('on');
      setTimeout(function(){o.classList.remove('on')},1800)}
    else alert(j.msg||'没存上');
  }).catch(function(){btn.textContent='保 存';btn.disabled=false;alert('网络不通，再试')});
}
"""


def ops_page(key):
    w = works()
    h = ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
         '<title>画 · 后台</title><style>' + OPS_CSS + '</style></head>',
         '<body data-k="' + H.escape(key) + '">']

    h.append('<div class="hd"><img src="/xin/m/avatar-s.png" alt="">'
             '<div class="nm">画<small>标 价 与 上 架</small></div></div>')

    for vol, sub, _ in VOLS:
        items = [w[p[0]] for p in DEF if p[2] == vol]
        if not items:
            continue
        h.append('<div class="vh">' + H.escape(vol) + '</div><div class="rule"></div>')
        for it in items:
            pid = it["id"]
            h.append('<div class="r" data-id="' + pid + '">'
                     '<img src="' + thumb(pid) + '" alt="">'
                     '<div class="m"><b>' + H.escape(it["t"]) + '</b><div class="sw">'
                     '<button class="' + ("on" if it["on"] else "") + '" onclick="tg(this,\'on\')">上架</button>'
                     '<button class="sd ' + ("on" if it["sold"] else "") + '" onclick="tg(this,\'on\')">已售</button>'
                     '</div></div>'
                     '<div class="pr"><input type="number" value="' + money(it["price"]) + '">'
                     '<label>元</label></div></div>')

    h.append('<button class="save" onclick="sv()">保 存</button>')
    h.append('<a class="back" href="/xin/boss/' + H.escape(key) + '">← 回工作台</a>')
    h.append('<div class="ok" id="ok">已 存 好</div>')
    h.append('<script>' + OPS_JS + '</script></body></html>')
    return "".join(h)


# ============================== 路由 ==============================
def install(app):
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    def _ok(k):
        return bool(k) and k == core.get("ops_key")

    @app.get("/xin/art", response_class=HTMLResponse)
    def _art():
        return HTMLResponse(page(), headers={"Cache-Control": "no-store"})

    @app.get("/xin/artops/{key}", response_class=HTMLResponse)
    def _artops(key: str):
        if not _ok(key):
            return HTMLResponse("<h2>没有入口</h2>", status_code=403)
        return HTMLResponse(ops_page(key), headers={"Cache-Control": "no-store"})

    @app.post("/xin/api/art/save")
    async def _art_save(req: Request):
        d = await req.json()
        if not _ok(d.get("key") or ""):
            return {"ok": 0, "msg": "没有权限"}
        items = []
        for x in (d.get("items") or []):
            pid = x.get("id") or ""
            if not pid:
                continue
            items.append({"id": pid,
                          "price": float(x.get("price") or 0),
                          "on": int(x.get("on") or 0),
                          "sold": int(x.get("sold") or 0)})
        core.set("art_works", json.dumps(items, ensure_ascii=False))
        return {"ok": 1}

    # ---------- 画作订单 ----------
    @app.post("/xin/api/art/pay")
    async def _art_pay(req: Request):
        """他说付好了：入库 + 立刻发邮件叫老师确认"""
        d = await req.json()
        pid = (d.get("art") or "").strip()
        w = works().get(pid)
        if not w:
            return {"ok": 0, "msg": "没有这幅画"}
        who = (d.get("who") or "").strip()[:20] or "有人"
        contact = (d.get("contact") or "").strip()[:40]
        note = (d.get("note") or "").strip()[:300]
        price = float(w["price"])
        c = _db()
        c.execute("""INSERT INTO art_ord(art_id,name,price,who,contact,note,status,created)
                     VALUES(?,?,?,?,?,?, 'claimed', ?)""",
                  (pid, w["t"], price, who, contact, note, core.now()))
        c.commit()
        c.close()
        _mail(pid, w["t"], price, who, contact, note)
        return {"ok": 1}

    @app.get("/xin/artpay/{key}", response_class=HTMLResponse)
    def _artpay(key: str):
        if not _ok(key):
            return HTMLResponse("<h2>没有入口</h2>", status_code=403)
        return HTMLResponse(pay_page(key), headers={"Cache-Control": "no-store"})

    @app.post("/xin/api/art/ord")
    async def _ord(req: Request):
        d = await req.json()
        if not _ok(d.get("key") or ""):
            return {"ok": 0}
        oid = int(d.get("id") or 0)
        st = (d.get("status") or "").strip()
        if st not in ("claimed", "done", "drop"):
            return {"ok": 0}
        c = _db()
        c.execute("UPDATE art_ord SET status=? WHERE id=?", (st, oid))
        c.commit()
        c.close()
        return {"ok": 1}


def _db():
    import sqlite3
    c = sqlite3.connect(core.DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    c = _db()
    c.execute("""CREATE TABLE IF NOT EXISTS art_ord(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        art_id TEXT, name TEXT, price REAL,
        who TEXT, contact TEXT, note TEXT,
        status TEXT DEFAULT 'claimed', created TEXT)""")
    c.commit()
    c.close()


def _mail(pid, name, price, who, contact, note):
    import os
    import subprocess
    import tempfile
    try:
        html = ('<div style="font-family:-apple-system,\'PingFang SC\',sans-serif;'
                'max-width:520px;margin:0 auto;padding:8px">'
                '<h2 style="color:#8a6b32;font-weight:600">有人要买「' + name + '」</h2>'
                '<p style="background:#f6f2ea;padding:14px;border-radius:8px;'
                'color:#2b2b2b;line-height:2">'
                ' 画：<b>' + name + '</b><br>'
                ' 价：<b>￥' + money(price) + '</b><br>'
                ' 谁：' + who + '<br>'
                ' 联系：' + (contact or "（没留）") + '<br>'
                ' 附言：' + (note or "（无）") +
                '</p>'
                '<p style="font-size:13px;color:#666">他说付好了。'
                '你去微信看一眼有没有这笔钱，收到了再点确认。</p>'
                '<p><a href="' + conf.u("/xin/artpay/")
                + (core.get("ops_key") or "") + '">去确认 ›</a></p></div>')
        fd, hp = tempfile.mkstemp(suffix=".html")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(html)
        subprocess.run([conf.PYBIN,
                        conf.SENDMAIL,
                        "--to", conf.OPS_EMAIL,
                        "--from-name", conf.MAIL_FROM,
                        "--subject", "有人要买「%s」 ￥%s" % (name, money(price)),
                        "--html", hp],
                       stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
        os.unlink(hp)
    except Exception as e:
        print("[art mail]", e)


def pay_page(key):
    c = _db()
    rows = c.execute("""SELECT * FROM art_ord WHERE status IN ('claimed','done')
                        ORDER BY (status='done'), id DESC LIMIT 60""").fetchall()
    c.close()
    todo = [r for r in rows if r["status"] == "claimed"]
    done = [r for r in rows if r["status"] == "done"]

    h = ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
         '<title>画的订单</title><style>' + OPS_CSS + '</style></head><body>']
    h.append('<div class="hd"><img src="/xin/m/avatar-s.png" alt="">'
             '<div class="nm">画的订单<small>说付好了 · 等你确认</small></div></div>')

    h.append('<div class="vh">等 你 确 认 · ' + str(len(todo)) + ' 单</div>'
             '<div class="rule"></div>')
    if not todo:
        h.append('<p style="font-size:16px;color:#8F8776;padding:16px 0">'
                 '现在没有。有人点「我付好了」，这里会出来。</p>')
    for r in todo:
        h.append('<div class="r" style="flex-wrap:wrap">'
                 '<img src="' + thumb(r["art_id"]) + '" alt="">'
                 '<div class="m"><b>' + H.escape(r["name"]) +
                 ' · ￥' + money(r["price"]) + '</b>'
                 '<div style="font-size:15px;color:#A79E8B;margin-top:7px;line-height:1.8">'
                 + H.escape(r["who"] or "有人") + '　'
                 + H.escape(r["contact"] or "没留联系方式") +
                 (('<br>' + H.escape(r["note"])) if r["note"] else '') + '</div>'
                 '<div class="sw"><button onclick="od(' + str(r["id"]) +
                 ',\'done\',this)">收 到 了</button>'
                 '<button class="sd" onclick="od(' + str(r["id"]) + ',\'drop\',this)">'
                 '不 要 了</button></div></div></div>')

    if done:
        h.append('<div class="vh" style="margin-top:40px">已 收 到 · ' + str(len(done)) + ' 单</div>'
                 '<div class="rule"></div>')
        for r in done:
            h.append('<div class="r" style="opacity:.62">'
                     '<img src="' + thumb(r["art_id"]) + '" alt="">'
                     '<div class="m"><b>' + H.escape(r["name"]) +
                     ' · ￥' + money(r["price"]) + '</b>'
                     '<div style="font-size:14.5px;color:#8F8776;margin-top:6px">'
                     + H.escape(r["who"] or "有人") + '　'
                     + (r["created"] or "")[:16] + '</div></div></div>')

    h.append('<a class="back" href="/xin/boss/' + H.escape(key) + '">← 回工作台</a>')
    h.append('<div class="ok" id="ok">好 了</div>')
    h.append('<script>'
             'function od(id,st,el){el.disabled=true;el.textContent="…";'
             'fetch("/xin/api/art/ord",{method:"POST",'
             'headers:{"Content-Type":"application/json"},'
             'body:JSON.stringify({key:"' + H.escape(key) + '",id:id,status:st})})'
             '.then(function(r){return r.json()}).then(function(j){'
             'if(j.ok){location.reload()}else{el.disabled=false;el.textContent="再试"}})'
             '.catch(function(){el.disabled=false;el.textContent="再试"})}'
             '</script></body></html>')
    return "".join(h)
