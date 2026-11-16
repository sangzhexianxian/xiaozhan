import re
import time
# -*- coding: utf-8 -*-
"""夜话 · 货架与设置
- 产品配置（价格 / 时长 / 原价划线 / 开关）存 settings.products
- 老师后台改价页  /xin/setup/{key}
- 粉丝门厅页      /xin  （由 app.py 让位后由此提供）
"""
import html as H
import json
import sqlite3

import core
import conf

# 默认货架（第一次跑就是这套）
DEF = {
    "voice": {"on": 1, "label": "聊一会儿", "sub": "语音 · 打个电话",
              "minutes": 20, "price": 99.0, "orig": 149.0},
    "video": {"on": 1, "label": "见一面", "sub": "视频 · 能看见人",
              "minutes": 20, "price": 199.0, "orig": 299.0},
    "chat": {"on": 1, "label": "说句话", "sub": "AI 分身 · 半夜也在",
             "unit": "句", "price": 1.0, "orig": 2.0},
    "week": {"on": 1, "label": "包一周", "sub": "数字分身 · 每天 20 条",
             "price": 29.9, "orig": 49.0, "quota": 20},
    "note": {"on": 1, "label": "写封信", "sub": "写一封给你 · 我念给你听",
             "price": 99.0, "orig": 149.0},
}
ORDER = ["voice", "video", "chat", "week", "note"]


def _c():
    c = sqlite3.connect(core.DB)
    c.row_factory = sqlite3.Row
    return c


def prods():
    """读配置，缺的用默认补上"""
    raw = core.get("products")
    d = {}
    if raw:
        try:
            d = json.loads(raw)
        except Exception:
            d = {}
    out = {}
    for k, v in DEF.items():
        cur = dict(v)
        if isinstance(d.get(k), dict):
            cur.update(d[k])
        out[k] = cur
    # 名字与说明只认代码里的（settings 里存的是旧名字，不能盖）
    for k in ORDER:
        if k in DEF:
            out[k]["label"] = DEF[k]["label"]
            out[k]["sub"] = DEF[k]["sub"]
    if float(out["note"].get("orig") or 0) <= float(out["note"].get("price") or 0):
        out["note"]["orig"] = DEF["note"]["orig"]
    # 包一周的说明跟着句数走
    try:
        out["week"]["sub"] = "数字分身 · 每天 %d 条" % int(out["week"].get("quota") or 20)
    except Exception:
        pass
    # 写信这一档的真钱在 price_reply / price_r1 / price_r2，展示跟着它走
    try:
        rp = core.get("price_reply")
        if rp:
            out["note"]["price"] = float(rp)
    except Exception:
        pass
    return out


def save(d):
    core.set("products", json.dumps(d, ensure_ascii=False))


def one(kind):
    return prods().get(kind) or dict(DEF.get(kind) or {})


CSS = """*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:#0a0a0a;color:#e8e0d0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;
  min-height:100vh;padding:calc(26px + env(safe-area-inset-top)) 20px calc(40px + env(safe-area-inset-bottom));
  max-width:520px;margin:0 auto}
h1{font-size:19px;font-weight:500;letter-spacing:3px;color:#f0e8d8;margin-bottom:6px}
.sub{font-size:12px;color:#7a736a;letter-spacing:.5px;margin-bottom:26px}
.card{background:rgba(255,255,255,.026);border:1px solid rgba(201,169,97,.14);
  border-radius:16px;padding:16px 16px 14px;margin-bottom:12px}
.row{display:flex;gap:10px;align-items:center;margin-bottom:10px}
.row:last-child{margin-bottom:0}
.nm{flex:1;font-size:14px;color:#ded5c4}
.nm small{display:block;font-size:11px;color:#6f695f;margin-top:3px;letter-spacing:.3px}
input[type=number],input[type=text]{background:rgba(255,255,255,.04);border:1px solid rgba(201,169,97,.16);
  color:#f0e8d8;border-radius:9px;padding:9px 10px;font-size:15px;font-family:inherit;text-align:center}
input[type=number]{width:76px}
input[type=text]{width:118px;text-align:left}
.unit{font-size:12px;color:#6f695f}
.hint{font-size:11px;color:#5f5a52;line-height:1.7;margin:6px 0 0}
.save{width:100%;margin-top:18px;padding:15px;border:none;border-radius:13px;font-size:16px;
  letter-spacing:4px;background:linear-gradient(135deg,#c9a961,#a8863f);color:#171208;font-weight:600;
  font-family:inherit}
.save:active{opacity:.85}
.ok{position:fixed;left:0;right:0;bottom:0;padding:14px;text-align:center;background:#1c6b4a;color:#eafaf2;
  font-size:14px;transform:translateY(100%);transition:.25s;z-index:50}
.ok.on{transform:translateY(0)}
.sw{position:relative;width:42px;height:24px;border-radius:12px;background:#2a2823;transition:.2s;flex:0 0 auto}
.sw.on{background:#c9a961}
.sw i{position:absolute;top:3px;left:3px;width:18px;height:18px;border-radius:50%;background:#8c8579;transition:.2s}
.sw.on i{left:21px;background:#1a1710}"""


def setup_page(key):
    tid = core.get("ops_key")
    if not key or key != tid:
        return "<h2 style='color:#888;padding:60px'>没有入口</h2>"
    p = prods()
    rows = []
    for k in ORDER:
        d = p[k]
        if k in ("voice", "video"):
            rows.append("""
<div class="card">
  <div class="row"><div class="nm">%s<small>%s</small></div>
    <div class="sw %s" data-k="%s" onclick="tg(this)"><i></i></div></div>
  <div class="row"><span class="unit">一次聊</span>
    <input type="number" min="5" max="180" step="5" data-k="%s" data-f="minutes" value="%s">
    <span class="unit">分钟</span></div>
  <div class="row"><span class="unit">现价 ¥</span>
    <input type="number" min="0" step="1" data-k="%s" data-f="price" value="%s">
    <span class="unit">原价 ¥</span>
    <input type="number" min="0" step="1" data-k="%s" data-f="orig" value="%s"></div>
  <div class="hint">原价填上会在粉丝那边划掉显示，不想显示就填 0</div>
</div>""" % (H.escape(d["label"]), H.escape(d["sub"]), "on" if d["on"] else "", k,
             k, d["minutes"], k, _n(d["price"]), k, _n(d["orig"])))
        else:
            extra = ""
            if k == "note":
                rp = core.get("price_reply") or "99"
                r1 = core.get("price_r1") or "39"
                r2 = core.get("price_r2") or "69"
                extra = """<div class="row"><span class="unit">回一封信 ¥</span>
    <input type="number" min="0" step="1" data-k="note" data-f="p_reply" value="%s">
    <span class="unit">100字 ¥</span>
    <input type="number" min="0" step="1" data-k="note" data-f="p_r1" value="%s"></div>
  <div class="row"><span class="unit">300字 ¥</span>
    <input type="number" min="0" step="1" data-k="note" data-f="p_r2" value="%s">
    <span class="unit" style="flex:1;text-align:right">代读两档</span></div>""" % (
                    _n(rp), _n(r1), _n(r2))
                price_row = ""
            elif k == "week":
                extra = """<div class="row"><span class="unit">¥</span>
    <input type="number" min="0" step="1" data-k="week" data-f="price" value="%s">
    <span class="unit">原价 ¥</span>
    <input type="number" min="0" step="1" data-k="week" data-f="orig" value="%s">
    <span class="unit">一周</span>
    <input type="number" min="1" step="1" data-k="week" data-f="quota" value="%s">
    <span class="unit">句</span></div>""" % (
                    _n(d["price"]), _n(d["orig"]), _n(d.get("quota") or 20))
                price_row = ""
            elif k == "chat":
                extra = """<div class="row"><span class="unit">一句 ¥</span>
    <input type="number" min="0" step="0.5" data-k="chat" data-f="price" value="%s">
    <span class="unit">原价 ¥</span>
    <input type="number" min="0" step="0.5" data-k="chat" data-f="orig" value="%s"></div>""" % (
                    _n(d["price"]), _n(d["orig"]))
                price_row = ""
            else:
                price_row = """<div class="row"><span class="unit">¥</span>
    <input type="number" min="0" step="1" data-k="%s" data-f="price" value="%s">
    <span class="unit">原价 ¥</span>
    <input type="number" min="0" step="1" data-k="%s" data-f="orig" value="%s"></div>""" % (
                    k, _n(d["price"]), k, _n(d["orig"]))
            rows.append("""
<div class="card">
  <div class="row"><div class="nm">%s<small>%s</small></div>
    <div class="sw %s" data-k="%s" onclick="tg(this)"><i></i></div></div>
  %s%s
  <div class="hint">%s</div>
</div>""" % (H.escape(d["label"]), H.escape(d["sub"]), "on" if d["on"] else "", k,
             extra, price_row,
             ("这一档的门厅价格＝回一封信的价格" if k == "note"
              else ("填 0 就在粉丝那边不显示这一项" if k != "chat" else ""))))

    import live as _lv
    cf = _lv.cfg()
    wd = ["日", "一", "二", "三", "四", "五", "六"]
    wds = "".join('<button class="wd%s" data-d="%d">%s</button>'
                  % (" on" if d in [int(x) for x in cf["days"]] else "", d, wd[d])
                  for d in range(7))
    _times = list(cf["times"]) + ["", "", "", ""]
    tms = "".join(
        '<input type="time" data-t="%d" value="%s" '
        'style="width:104px;text-align:center;padding:11px 6px">' % (i, t)
        for i, t in enumerate(_times[:6]))

    try:
        _up = _lv.slots(days=14)
    except Exception:
        _up = []
    _byday = {}
    for _x in _up:
        _byday.setdefault(_x["day"], []).append(_x["hm"])
    _prev = ""
    for _d in sorted(_byday)[:6]:
        _prev += ('<div class="pv"><b>%s</b><span>%s</span></div>'
                  % (_d[5:].replace("-", "/"), " · ".join(_byday[_d])))
    if not _prev:
        _prev = '<div class="pv"><span>这段时间还没开出来</span></div>'

    return """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>价格与时间</title><style>%s
.tmwrap{display:flex;flex-wrap:wrap;gap:8px}
.pv{display:flex;justify-content:space-between;padding:9px 0;font-size:13.5px;
 border-bottom:1px solid rgba(255,255,255,.05)}
.pv b{color:#c9a961;font-weight:500;flex:0 0 58px}
.pv span{color:#8c8179;flex:1;text-align:right}
.wd{background:rgba(255,255,255,.04);border:1px solid rgba(201,169,97,.16);color:#B9AD95;
 border-radius:10px;padding:9px 0;width:40px;font-size:14px;font-family:inherit}
.wd.on{background:#C9A961;color:#171208;border-color:#C9A961;font-weight:600}
</style></head><body>
<div style="display:flex;align-items:center;gap:11px;margin:0 0 18px"><img src="/xin/m/avatar-s.png" alt="" style="width:42px;height:42px;border-radius:21px;object-fit:cover;border:1px solid rgba(201,169,97,.4)"><div style="font-size:12.5px;color:#A79C89;letter-spacing:.1em">我的小站</div></div>
<h1>价格与时间</h1>
<div class="sub">改完点最下面保存，粉丝那边立刻变</div>

<div class="card">
  <div class="row"><div class="nm">开放时段<small>粉丝只能在你开放的时间里约你</small></div></div>
  <div class="row" style="flex-wrap:wrap;gap:7px" id="wds">%s</div>
  <div class="hint" style="margin:2px 0 9px">点一下时间格子，手机上会转出滚轮，选就行</div>
  <div class="tmwrap">%s</div>
  <div class="hint">留空的就是不要。最多六个点。</div>
</div>

%s
<button class="save" onclick="sv()">保 存</button>

<div class="card" style="margin-top:22px;border-color:rgba(201,169,97,.28)">
  <div class="row"><div class="nm">换一条新链接<small>怀疑链接被人转出去了，就用这个</small></div></div>
  <div class="hint" style="margin-bottom:10px">
    换完旧链接立刻作废。你自己不会掉线，收藏的 /xin/b 照样能进。
  </div>
  <button onclick="rot()" style="width:100%%;padding:13px;border-radius:10px;
    border:1px solid rgba(201,169,97,.4);background:transparent;color:#c9a961;
    font-size:14px;letter-spacing:.1em;font-family:inherit">换 一 条 新 链 接</button>
  <div id="rotout" style="font-size:12.5px;color:#8c8579;margin-top:10px;line-height:1.9"></div>
</div>

<div class="card">
  <div class="row"><div class="nm">这条链接就是钥匙<small>别转给别人</small></div></div>
  <div class="hint" style="line-height:2;margin-top:6px">
    换手机、清了浏览器之后，用微信收藏里那条<b style="color:#c9a961">长链接</b>再打开一次，
    这台设备就重新记住了。<br>
    真找不到了，就点上面那个「换一条新链接」，请人给你发一条新的。
  </div>
</div>

<div class="card">
  <div class="row"><div class="nm">提醒发到哪<small>有人付钱、有人约、有人写信的时候</small></div></div>
  <div class="row"><span class="unit">邮箱</span>
    <input type="text" id="nmail" placeholder="你的邮箱" style="width:100%%"></div>
  <div class="row"><span class="unit">企微</span>
    <input type="text" id="nwecom" placeholder="群机器人地址（可选 · 最快）" style="width:100%%"></div>
  <div class="hint">企微最快——手机微信会直接弹一条。留空就只发邮箱。<br>
    邮箱大概一分钟到。企微地址在群里「添加机器人」那里复制。</div>
  <button onclick="svNotify()" style="width:100%%;margin-top:12px;padding:13px;border-radius:10px;
    border:1px solid rgba(201,169,97,.4);background:transparent;color:#c9a961;
    font-size:14px;letter-spacing:.1em;font-family:inherit">保 存</button>
  <div id="nok" style="font-size:12.5px;color:#8c8579;margin-top:9px;line-height:1.9"></div>
</div>

<div class="card">
  <div class="row"><div class="nm">接下来两周<small>粉丝现在能约到这些</small></div></div>
  <div style="margin-top:4px">%s</div>
</div>

<div class="hint" style="margin-top:16px;text-align:center">
  <a href="/xin/boss/%s" style="color:#8c8579;text-decoration:none">回工作台</a>
</div>
<div class="ok" id="ok">已保存</div>
<script>
var P = %s;
function tg(el){ el.classList.toggle('on'); }
document.querySelectorAll('.wd').forEach(function(b){ b.onclick=function(){ b.classList.toggle('on'); }; });
function _k(){var a=location.pathname.split('/');return a[a.length-1]||''}
fetch('/xin/api/notify?key='+encodeURIComponent(_k()))
 .then(function(r){return r.json()}).then(function(j){
   var a=document.getElementById('nmail'), b=document.getElementById('nwecom');
   if(a&&j.mail)a.value=j.mail; if(b&&j.wecom)b.value=j.wecom;
 });
function svNotify(){
  var ok=document.getElementById('nok');
  ok.textContent='正在存…';
  fetch('/xin/api/notify/save',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({key:_k(),
      mail:(document.getElementById('nmail')||{}).value||'',
      wecom:(document.getElementById('nwecom')||{}).value||''})})
  .then(function(r){return r.json()}).then(function(j){
    ok.textContent = j.ok ? '存好了。下次有人付钱，就会发到这儿。' : (j.msg||'没存上');
    if(j.ok) ok.style.color='#7fbf9a';
  }).catch(function(){ok.textContent='网络不通，再试'});
}
function sv(){
  var d = JSON.parse(JSON.stringify(P));
  document.querySelectorAll('.sw').forEach(function(s){
    d[s.dataset.k].on = s.classList.contains('on') ? 1 : 0;
  });
  document.querySelectorAll('input[data-k]').forEach(function(i){
    var v = parseFloat(i.value); if (isNaN(v)) v = 0;
    d[i.dataset.k][i.dataset.f] = v;
  });
  var days=[], times=[];
  document.querySelectorAll('.wd.on').forEach(function(b){ days.push(parseInt(b.dataset.d)); });
  document.querySelectorAll('input[data-t]').forEach(function(i){
    var v=(i.value||'').trim(); if(v) times.push(v); });
  if(!days.length){ alert('至少要开放一天'); return; }
  if(!times.length){ alert('至少要给一个时间点'); return; }
  fetch('/xin/api/slots/save', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({key:'%s', days:days, times:times})}).then(function(r){return r.json();});
  fetch('/xin/api/prod/save', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({key:'%s', data:d})}).then(function(r){return r.json();})
    .then(function(j){
      if (j.ok) { var o=document.getElementById('ok'); o.classList.add('on');
        setTimeout(function(){o.classList.remove('on')},1600); }
      else alert(j.msg || '没存上');
    });
}
function rot(){
  if(!confirm('确定换新链接？旧链接会立刻失效。')) return;
  fetch('/xin/api/rotate',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({key:'%s'})}).then(function(r){return r.json();}).then(function(j){
    if(!j.ok){ document.getElementById('rotout').textContent=j.msg||'没换成'; return; }
    document.getElementById('rotout').innerHTML=
      '换好了。新链接：<br><b style="color:#e8c07a;word-break:break-all">'+j.link+'</b><br>'
      +'长按复制，发到文件传输助手存着。收藏的 <b>'+j.short+'</b> 照样能用。';
  });
}
</script><script>try{var p=location.pathname;if(/^\\/xin\\/(boss|setup|pay|orders|liveops|chatlog)\\//.test(p))history.replaceState(null,'','/xin/b');}catch(e){}</script></body></html>""" % (CSS, wds, tms, "".join(rows),
       _prev, key, json.dumps(p, ensure_ascii=False), key, key, key)


def _n(v):
    try:
        f = float(v)
        return ("%d" % f) if abs(f - int(f)) < 0.001 else ("%.1f" % f)
    except Exception:
        return "0"


def hall_page(req=None):
    """粉丝门厅：一屏看到三个选择"""
    tid = core.get("ops_key")
    p = prods()
    brand = core.get("brand") or "老师"
    cards = []
    INC = {
        "voice": "30 分钟 · 一对一 · 想说什么说什么",
        "video": "30 分钟 · 面对面 · 你能看见我",
        "week": "不是真人 · 是我的声音和口气 · 半夜也能聊",
        "note": "手写一封 · 录成声音发你",
        "chat": "一句一句 · 随时能聊",
    }
    LINK = {"voice": "/xin/live", "video": "/xin/live", "chat": "/xin/chat",
            "week": "/xin/chat", "note": "/xin/liuyan"}
    for k in ORDER:
        d = p[k]
        if not d.get("on"):
            continue
        if k in ("voice", "video"):
            amt = "¥%s" % _n(d["price"])
            unit = " / %s 分钟" % d["minutes"]
        elif k == "chat":
            amt = "¥%s" % _n(d["price"])
            unit = " / 句"
        else:
            amt = "¥%s" % _n(d["price"])
            unit = ""
        cut = ""
        if d.get("orig") and float(d["orig"]) > float(d["price"]):
            cut = '<i>¥%s</i>' % _n(d["orig"])
        cards.append("""
<a class="p" href="%s">
  <div class="pl">
    <div class="pn">%s</div>
    <div class="ps">%s</div>
    <div class="pi">%s</div>
  </div>
  <div class="pr"><b>%s</b><span>%s</span>%s</div>
</a>""" % (LINK.get(k, "/xin/live"), H.escape(d["label"]), H.escape(d["sub"]),
           INC.get(k, ""), amt, unit, cut))

    # 画廊：单独一张卡，不参与货架价格体系
    try:
        import art as _art
        _ws = [x for x in _art.works().values() if x["on"] and not x["sold"]]
        _low = min([x["price"] for x in _ws]) if _ws else 0
        cards.append("""
<a class="p" href="/xin/art">
  <div class="pl">
    <div class="pn">买一幅画</div>
    <div class="ps">原作 · 限量</div>
    <div class="pi">都是原件 · 看中了直接跟我聊 · 谈妥再付</div>
  </div>
  <div class="pr"><b>\u00a5%s</b><span>起</span></div>
</a>""" % (_art.money(_low) if _low else "\u2014"))
    except Exception as _e:
        print("[hall] art card failed:", _e)

    return """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>%s</title><style>%s
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:#0B0A08;color:#F2ECDF;
 font-family:"Songti SC","Noto Serif CJK SC","Source Han Serif SC",Georgia,serif;
 font-size:16.5px;line-height:1.95;letter-spacing:.02em;
 padding:calc(40px + env(safe-area-inset-top)) 26px calc(70px + env(safe-area-inset-bottom));
 max-width:580px;margin:0 auto;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}

.hero{text-align:center;padding:12px 0 0}
.hero img{width:104px;height:104px;border-radius:52px;object-fit:cover;
 border:1px solid rgba(201,169,97,.4)}
.hero h1{margin-top:22px;font-size:27px;letter-spacing:.24em;color:#F7F2E6;
 font-weight:600;line-height:1.3}
.role{font-size:13px;color:#A87F4A;letter-spacing:.4em;margin-top:12px}
.proof{font-size:14px;color:#8F8776;letter-spacing:.08em;margin-top:10px}

.say{margin:44px 0 8px;text-align:center;font-size:16.5px;color:#C5BCA8;
 line-height:2.2;letter-spacing:.08em}
.say::before,.say::after{content:"";display:block;width:44px;height:1px;
 margin:22px auto;background:rgba(201,169,97,.35)}

.sec{font-size:13.5px;color:#A87F4A;letter-spacing:.32em;margin:52px 0 4px}
.sec em{font-style:normal;color:#5C4A2C;margin-right:12px}
.rule{height:1px;margin:0 0 26px;
 background:linear-gradient(90deg,rgba(201,169,97,.5),rgba(201,169,97,.04))}

.p{display:flex;align-items:flex-start;gap:18px;border:1px solid rgba(201,169,97,.24);border-radius:4px;
 padding:26px 24px;margin-bottom:16px}
.p:active{border-color:rgba(201,169,97,.5)}
.pl{flex:1;min-width:0}
.pn{font-size:22px;color:#F7F2E6;letter-spacing:.16em;font-weight:600;white-space:nowrap}
.ps{font-size:15.5px;color:#A79E8B;margin-top:9px;letter-spacing:.04em}
.pi{font-size:15px;color:#8F8776;margin-top:7px;line-height:1.8}
.pr{text-align:right;flex:0 0 auto;padding-top:2px}
.pr b{font-size:26px;color:#E6CD91;font-weight:400;letter-spacing:.02em}
.pr span{font-size:13.5px;color:#8F8776;display:block;margin-top:2px}
.pr i{display:block;font-size:14px;color:#6B6355;text-decoration:line-through;
 font-style:normal;margin-top:3px}

.flow{border:1px solid rgba(201,169,97,.2);border-radius:4px}
.flow>div{display:flex;align-items:baseline;gap:16px;padding:22px 24px;
 border-bottom:1px solid rgba(201,169,97,.12)}
.flow>div:last-child{border-bottom:none}
.flow b{font-size:15px;color:#A87F4A;font-weight:400;flex:0 0 auto;letter-spacing:.1em}
.flow span{font-size:18px;color:#F2ECDF;letter-spacing:.14em;flex:0 0 auto}
.flow i{flex:1;font-style:normal;font-size:15px;color:#8F8776;text-align:right}

.faq>div{padding:20px 0;border-bottom:1px solid rgba(201,169,97,.1)}
.faq>div:last-child{border-bottom:none}
.faq b{display:block;font-size:17.5px;color:#F2ECDF;font-weight:400;letter-spacing:.1em}
.faq p{font-size:15px;color:#8F8776;margin-top:8px;line-height:1.95}

.foot{text-align:center;font-size:14px;color:#6B6355;margin-top:60px;
 line-height:2.2;letter-spacing:.06em}
.foot .ln{width:44px;height:1px;background:rgba(201,169,97,.25);margin:0 auto 26px}
.foot a{color:#8D6C42;display:inline-block;margin-top:10px;padding:10px 0;
 border-top:1px solid rgba(201,169,97,.16);min-width:210px}
</style></head><body>
    <div class="hero">
      <img src="/xin/m/avatar-s.png" alt="">
      <h1>%s</h1>
      <div class="role">作品　声音　文字</div>
      <div class="proof">每一件，都是亲手做的</div>
    </div>

    <div class="say">
      山是走出来的，字是念出来的。<br>
      想说什么，我在这儿听着。
    </div>

    <div class="sec"><em>一</em>找 我 做 什 么</div><div class="rule"></div>
    %s

    <div class="sec"><em>二</em>怎 么 走</div><div class="rule"></div>
    <div class="flow">
      <div><b>一</b><span>选一样</span><i>上面四样，挑一样</i></div>
      <div><b>二</b><span>付钱</span><i>微信扫码，不用注册</i></div>
      <div><b>三</b><span>等</span><i>约的准点开始；信我一天内回</i></div>
    </div>

    <div class="sec"><em>三</em>你 可 能 想 问</div><div class="rule"></div>
    <div class="faq">
      <div><b>钱怎么付</b><p>微信扫码转账。付完点一下「我付好了」，我这边立刻就知道了。</p></div>
      <div><b>多久能回</b><p>信我一般一天内回。约的时间就是你挑的那个点，准点开始。</p></div>
      <div><b>别人看得见吗</b><p>看不见。你说的只有我一个人看，六十天后自动删掉。<br>不聊政治、不聊违法的事，也别把这儿当心理咨询——撑不住了请打 12356。</p></div>
      <div><b>不满意怎么办</b><p>开始之前，全额退。开始过了，退一半。跟我说一声就行。</p></div>
    </div>

    <div class="foot">
      <div class="ln"></div>
      所有话都只在你我之间<br>
      <a href="/xin/me">%s</a>
    </div>
</body></html>""" % (H.escape(brand), CSS, H.escape(brand), "".join(cards), _me_line(req))


def _me_line(req):
    """底部那句：登录了就报余额"""
    try:
        import acct
        uid = acct.uid_of(req) if req is not None else 0
        if uid:
            u = acct.me(uid)
            return "我账上 ¥%s　·　我的" % _n(u["balance"])
    except Exception:
        pass
    return "我的"


def install(app):
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    @app.get("/xin/", response_class=HTMLResponse)
    def _hall(req: Request):
        if core.get("paused") == "1":
            return HTMLResponse(
                "<div style='background:#0a0a0a;color:#918d85;font-family:sans-serif;"
                "display:flex;align-items:center;justify-content:center;height:100vh;"
                "margin:0;text-align:center;line-height:2;font-size:15px'>"
                "这周排满了<br><span style='font-size:13px'>下周再来</span></div>",
                headers={"Cache-Control": "no-store"})
        return HTMLResponse(hall_page(req), headers={"Cache-Control": "no-store"})

    @app.get("/xin/setup/{key}", response_class=HTMLResponse)
    def _setup(key: str):
        return setup_page(key)

    @app.post("/xin/api/prod/save")
    async def _save(req: Request):
        d = await req.json()
        if (d.get("key") or "") != core.get("ops_key"):
            return {"ok": 0, "msg": "没有权限"}
        data = d.get("data") or {}
        cur = prods()
        for k in ORDER:
            if isinstance(data.get(k), dict):
                for f in ("on", "minutes", "price", "orig", "quota"):
                    if f in data[k]:
                        try:
                            cur[k][f] = (int(data[k][f]) if f in ("on", "minutes", "quota")
                                         else round(float(data[k][f]), 2))
                        except Exception:
                            pass
        note = data.get("note") or {}
        for f, sk in (("p_reply", "price_reply"), ("p_r1", "price_r1"), ("p_r2", "price_r2")):
            if f in note:
                try:
                    core.set(sk, str(int(round(float(note[f])))))
                except Exception:
                    pass
        save(cur)
        return {"ok": 1, "data": prods()}



    @app.get("/xin/api/notify")
    def _notify_get(key: str = ""):
        if (key or "") != (core.get("ops_key") or ""):
            return {"ok": 0}
        return {"ok": 1,
                "mail": core.get("notify_mail") or "",
                "wecom": core.get("notify_wecom") or ""}

    @app.post("/xin/api/notify/save")
    async def _notify_save(req: Request):
        d = await req.json()
        if (d.get("key") or "") != (core.get("ops_key") or ""):
            return {"ok": 0, "msg": "没有权限"}
        core.set("notify_mail", (d.get("mail") or "").strip()[:120])
        core.set("notify_wecom", (d.get("wecom") or "").strip()[:300])
        return {"ok": 1}

    @app.post("/xin/api/rotate")
    async def _rotate(req: Request):
        """怀疑链接漏出去了，一键作废"""
        d = await req.json()
        if (d.get("key") or "") != core.get("ops_key"):
            return {"ok": 0, "msg": "没有权限"}
        new1 = core.new_token(10)
        new2 = core.new_token(10)
        core.set("ops_key", new1)
        if core.get("desk_key"):
            core.set("desk_key", new2)
        return {"ok": 1, "link": conf.SITE + "/xin/boss/" + new1,
                "short": conf.SITE + "/xin/b"}

    @app.post("/xin/api/slots/save")
    async def _slots_save(req: Request):
        d = await req.json()
        if (d.get("key") or "") != core.get("ops_key"):
            return {"ok": 0, "msg": "没有权限"}
        import live as _lv
        days = [int(x) for x in (d.get("days") or []) if str(x).isdigit()]
        times = [str(x).strip() for x in (d.get("times") or []) if str(x).strip()]
        times = sorted([t for t in times if len(t) == 5 and t[2] == ":"] )
        if not days or not times:
            return {"ok": 0, "msg": "至少一天一个时间点"}
        _lv.set_cfg({"days": days, "times": times})
        return {"ok": 1, "days": days, "times": times}

    @app.get("/xin/api/prod")
    def _get(key: str = ""):
        if key and key != core.get("ops_key"):
            return {"ok": 0}
        return {"ok": 1, "data": prods()}
