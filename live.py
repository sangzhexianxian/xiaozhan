# -*- coding: utf-8 -*-
"""夜话 · 真人预约（语音 / 视频）
挂载：app.py 末尾  import live; live.install(APP)
"""
import json
import os
import sqlite3
import time

import core
import acct

SLOT_MIN = 20
PRICE = {"voice": 99.0, "video": 199.0}


def price_of(kind):
    try:
        import shop
        v = float(shop.one(kind).get("price") or 0)
        return v if v > 0 else PRICE.get(kind, 0)
    except Exception:
        return PRICE.get(kind, 0)


def mins_of(kind):
    try:
        import shop
        m = int(shop.one(kind).get("minutes") or 0)
        return m if m > 0 else SLOT_MIN
    except Exception:
        return SLOT_MIN
LABEL = {"voice": "语音 20 分钟", "video": "视频 20 分钟"}
WD = ["一", "二", "三", "四", "五", "六", "日"]

DEFAULT_SLOTS = {"days": [2, 4, 6], "times": ["20:00", "20:40", "21:20"]}


def _c():
    c = sqlite3.connect(core.DB)
    c.row_factory = sqlite3.Row
    return c


def _init():
    c = _c()
    try:
        c.execute("ALTER TABLE booking ADD COLUMN token TEXT DEFAULT ''")
    except Exception:
        pass
    for col, ddl in (("topic", "TEXT DEFAULT ''"),):
        try:
            c.execute("ALTER TABLE booking ADD COLUMN %s %s" % (col, ddl))
        except Exception:
            pass
    try:
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_booking_token ON booking(token)")
    except Exception:
        pass
    c.commit()
    c.close()


_init()


def cfg():
    v = core.get("live_slots")
    if not v:
        return dict(DEFAULT_SLOTS)
    try:
        d = json.loads(v)
        d.setdefault("days", DEFAULT_SLOTS["days"])
        d.setdefault("times", DEFAULT_SLOTS["times"])
        return d
    except Exception:
        return dict(DEFAULT_SLOTS)


def set_cfg(d):
    core.set("live_slots", json.dumps(d, ensure_ascii=False))


def _dt(s):
    """'2026-11-18 20:00' -> struct_time"""
    return time.strptime(s, "%Y-%m-%d %H:%M")


def slots(days=10):
    """生成未来可约时段（已排满的跳过）"""
    cf = cfg()
    c = _c()
    taken = set()
    for r in c.execute("SELECT slot FROM booking WHERE status IN ('booked','done')"):
        taken.add(r["slot"])
    c.close()
    out = []
    now = time.time()
    for i in range(days):
        t = time.localtime(now + i * 86400)
        if i == 0 and t.tm_hour >= 21:
            continue
        if int(time.strftime("%w", t)) not in [int(x) for x in cf["days"]]:
            continue
        d = time.strftime("%Y-%m-%d", t)
        w = WD[(t.tm_wday) % 7]
        for hm in cf["times"]:
            s = d + " " + hm
            if _dt(s) <= time.localtime() and time.mktime(_dt(s)) <= now:
                continue
            if s in taken:
                continue
            out.append({"slot": s, "day": d, "hm": hm, "wd": w,
                        "left": int((time.mktime(_dt(s)) - now) / 60)})
    return out


def is_guest(uid):
    try:
        c = _c()
        r = c.execute("SELECT phone FROM usr WHERE id=?", (uid,)).fetchone()
        c.close()
        return bool(r and (r["phone"] or "").startswith("g_"))
    except Exception:
        return False


def book(uid, slot, kind, topic="", skip_gap=False):
    if kind not in PRICE:
        return {"ok": 0, "msg": "类型不对"}
    try:
        st = _dt(slot)
    except Exception:
        return {"ok": 0, "msg": "时间格式不对"}
    if not skip_gap and time.mktime(st) < time.time() + 1800:
        return {"ok": 0, "msg": "这个点太近了，换一个"}
    c = _c()
    if c.execute("SELECT 1 FROM booking WHERE slot=? AND status IN ('booked','done')",
                 (slot,)).fetchone():
        c.close()
        return {"ok": 0, "msg": "这个点刚被人约走了"}
    c.close()
    amt = price_of(kind)
    _guest = is_guest(uid)
    if _guest:
        nb = 0.0
        _st = "demo"
    else:
        okc, nb = acct.charge(uid, amt, "live", slot)
        if not okc:
            return {"ok": 0,
                    "msg": "你账上还有 %.0f 元，这一场要 %.0f 元，还差 %.0f 元"
                           % (nb, amt, amt - nb),
                    "need": round(amt - nb, 2), "bal": round(nb, 2), "amount": amt}
        _st = "booked"
    tok = core.new_token(10)
    c = _c()
    c.execute("INSERT INTO booking(uid,slot,kind,minutes,amount,status,created,token,topic)"
              " VALUES(?,?,?,?,?,?,?,?,?)",
              (uid, slot, kind, mins_of(kind), amt, _st, core.now(), tok,
               (topic or "").strip()[:200]))
    c.commit()
    bid = c.execute("SELECT last_insert_rowid() i").fetchone()["i"]
    c.close()
    return {"ok": 1, "id": bid, "balance": nb, "token": tok}


def instantly(uid, kind, topic=""):
    """他现在能接，马上开始"""
    import time as _t
    c = _c()
    # 同一个人一天只给一次，防止反复按
    n = c.execute("""SELECT COUNT(*) n FROM booking WHERE uid=? AND status IN ('booked','done')
                     AND substr(slot,1,10)=?""",
                  (uid, _t.strftime("%Y-%m-%d"))).fetchone()["n"]
    c.close()
    if n >= 6:
        return {"ok": 0, "msg": "今天已经约得够多了，明天再来"}
    t = _t.localtime(_t.time() + 120)
    slot = _t.strftime("%Y-%m-%d %H:%M", t)
    r = book(uid, slot, kind, topic, skip_gap=True)
    if r.get("ok"):
        r["instant"] = 1
    return r


def boss_online():
    """老师最近 6 分钟内打开过值班室就算在"""
    v = core.get("boss_seen") or ""
    if not v:
        return 0
    try:
        import time as _t
        return 1 if (_t.time() - float(v)) < 360 else 0
    except Exception:
        return 0


def my(uid):
    c = _c()
    rows = c.execute("SELECT * FROM booking WHERE uid=? ORDER BY id DESC LIMIT 20",
                     (uid,)).fetchall()
    c.close()
    out = []
    for r in rows:
        out.append({"id": r["id"], "slot": r["slot"], "kind": r["kind"],
                    "label": LABEL.get(r["kind"], ""), "amount": r["amount"],
                    "status": r["status"], "token": r["token"] or "",
                    "topic": r["topic"] if "topic" in r.keys() else ""})
    return out


# ---------------------------------------------------------------- 页面
CSS = """
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:#0a0a0a;color:#e8e2d6;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Noto Sans CJK SC",sans-serif;
 line-height:1.8;-webkit-font-smoothing:antialiased}
.wrap{max-width:520px;margin:0 auto;padding:32px 22px 60px}
h1{font-family:"Songti SC","Noto Serif CJK SC",serif;font-size:23px;font-weight:600;
 letter-spacing:.1em;color:#f2ede2;margin-bottom:6px}
.sub{font-size:12px;color:#6d675e;letter-spacing:.14em;margin-bottom:26px}
.tab{display:flex;border:1px solid rgba(201,169,97,.22);border-radius:4px;overflow:hidden;margin-bottom:22px}
.tab div{flex:1;text-align:center;padding:13px 0;font-size:14px;color:#8d8578;cursor:pointer;
 background:rgba(255,255,255,.02);letter-spacing:.06em}
.tab div.on{background:rgba(201,169,97,.16);color:#e8c07a}
.tab b{display:block;font-size:17px;font-weight:500;margin-top:2px}
.dgroup{margin-bottom:18px}
.dgroup+.dgroup{margin-top:24px;padding-top:20px;border-top:1px solid rgba(255,255,255,.06)}
.dh{font-size:12.5px;color:#c9a961;letter-spacing:.1em;margin-bottom:9px}
.slots{display:flex;gap:9px;flex-wrap:wrap}
.slots button{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.1);color:#b9ad95;
 border-radius:4px;padding:11px 16px;font-family:inherit;font-size:14.5px;cursor:pointer;min-width:92px}
.slots button.on{border-color:#c9a961;background:rgba(201,169,97,.2);color:#f2ede2;font-weight:600;
 box-shadow:inset 0 0 0 1px rgba(201,169,97,.35)}
.go{width:100%;background:#c9a961;color:#0a0a0a;border:0;border-radius:4px;font-family:inherit;
 font-size:15px;font-weight:600;padding:15px;letter-spacing:.1em;cursor:pointer;margin-top:20px}
.go:disabled{opacity:.35}
.ghost{display:block;width:100%;text-align:center;background:transparent;border:1px solid rgba(201,169,97,.3);
 color:#c9a961;border-radius:4px;font-family:inherit;font-size:14px;padding:13px;letter-spacing:.08em;
 cursor:pointer;margin-top:12px;text-decoration:none}
.hint{font-size:12px;color:#6d675e;line-height:1.95;margin-top:16px}
.hint b{color:#b9ad95}
.box{border:1px solid rgba(201,169,97,.25);border-radius:5px;padding:20px 18px;margin-bottom:14px}
.ok{text-align:center;padding:26px 18px}
.ok .big{font-size:30px;color:#e8c07a;font-weight:300;letter-spacing:.04em}
.ok .t1{font-size:14px;color:#b9ad95;margin-top:10px;line-height:2}
.mine{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);font-size:13.5px}
.mine .s{font-size:11.5px;color:#8d8578}
.err{color:#e8a49b;font-size:12.5px;margin-top:10px;min-height:18px}
a{color:#c9a961;text-decoration:none}
.tab b i{font-size:11px;color:#5a554d;text-decoration:line-through;font-style:normal;margin-left:5px}
"""

BODY = """
<div style="display:flex;align-items:center;gap:11px;margin:0 0 18px"><img src="/xin/m/avatar-s.png" alt="" style="width:42px;height:42px;border-radius:21px;object-fit:cover;border:1px solid rgba(201,169,97,.4)"><div style="font-size:12.5px;color:#A79C89;letter-spacing:.1em">我的小站</div></div>
<div class="wrap"><div id="box">正在读取…</div></div>
<script>
var BASE='/xin', KIND='voice', PICK='';
var PRICE={voice:99,video:199};

function api(p,o){
  return fetch(BASE+p,o?{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(o),credentials:'same-origin'}:{credentials:'same-origin'})
    .then(function(r){return r.json();});
}
function H(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}

function draw(D){
  var box=document.getElementById('box');
  if(!D.login){
    box.innerHTML='<h1>约他说话</h1><div class="sub">要 先 登 录</div>'+
      '<div class="box"><div class="t1" style="font-size:13.5px;color:#b9ad95">'+
      '约真人，得先登录，钱才记在你账上。</div></div>'+
      (D.guest ? '' : '<a class="go" style="display:block;text-align:center" href="/xin/me">充值</a>')+
      '<div class="hint"><a href="/xin/chat">← 先跟分身说两句</a></div>';
    return;
  }
  var pr = D.prices || {};
  function pv(k){ return pr[k] ? pr[k].price : PRICE[k]; }
  function pm(k){ return pr[k] ? pr[k].minutes : 20; }
  function pl(k){ return pr[k] ? pr[k].label : (k === 'voice' ? '语音' : '视频'); }
  function po(k){
    var o = pr[k] ? parseFloat(pr[k].orig) : 0, p = parseFloat(pv(k));
    return (o > p) ? '<i>￥' + o + '</i>' : '';
  }
  var soon=null;
  (D.mine||[]).forEach(function(r){
    if(r.status!=='booked'||!r.token) return;
    var t=new Date((r.slot||'').replace(/-/g,'/')).getTime();
    var mins=(t-Date.now())/60000;
    if(mins<=12 && mins>-40) soon={r:r, mins:Math.round(mins)};
  });
  var h='<h1>约他说话</h1><div class="sub">' + pm(KIND) + ' 分 钟 · 一 个 人</div>';
  if(soon){
    h+='<a href="/xin/join/'+soon.r.token+'" style="display:block;text-decoration:none;'
      +'background:linear-gradient(135deg,#c9a961,#a8863f);color:#1a1409;border-radius:14px;'
      +'padding:16px;text-align:center;margin-bottom:18px;font-size:15px;letter-spacing:.08em">'
      +'<b style="display:block;font-size:17px;margin-bottom:3px">'
      +(soon.mins>0?('还有 '+soon.mins+' 分钟就到'):'就是这一刻')
      +'</b>点这里进去等他</a>';
  }
  h+='<div class="tab"><div class="'+(KIND==='voice'?'on':'')+'" data-k="voice">'+pl('voice')+
     '<b>￥'+pv('voice')+po('voice')+'</b></div>'+
     '<div class="'+(KIND==='video'?'on':'')+'" data-k="video">'+pl('video')+
     '<b>￥'+pv('video')+po('video')+'</b></div></div>';
  h+='<div class="box" style="margin-bottom:16px"><div class="t1" style="font-size:13px;color:#b9ad95">'
     +'想聊点什么？（可以不填，他会先看）</div>'
     +'<textarea id="tpc" maxlength="200" placeholder="比如：我妈最近睡不着，我该怎么劝她" '
     +'style="width:100%;margin-top:9px;min-height:70px;padding:11px;border-radius:9px;'
     +'border:1px solid rgba(201,169,97,.2);background:rgba(255,255,255,.04);color:#e8e0d0;'
     +'font-family:inherit;font-size:14px;resize:vertical"></textarea></div>';
  if(D.online){
    h+='<a class="go" id="now" style="display:block;text-align:center;margin-bottom:14px;'
      +'background:linear-gradient(135deg,#c9a961,#a8863f)">他 现 在 在 · 现 在 就 约</a>';
  }
  if (D.guest) {
    h+='<div class="hint" style="margin:0 0 18px;color:#c9a961">'+
       '体验模式 ｜ 先约上看，真要付钱时再登录　到点前十分钟，他的微信会出现在这里</div>';
  } else {
    h+='<div class="hint" style="margin:0 0 18px">我账上 ￥'+D.balance+
       '　<a href="/xin/me" style="color:#c9a961">充值</a>　到点前十分钟，这里会出现他的微信</div>';
  }
  if(!D.slots.length){
    h+='<div class="box"><div class="t1" style="font-size:13.5px;color:#b9ad95">这几天都排满了。<br>过两天再来看看。</div></div>';
  } else {
    var cur='';
    D.slots.forEach(function(s){
      if(s.day!==cur){ if(cur) h+='</div>'; h+='<div class="dgroup"><div class="dh">'+s.day+'　周'+s.wd+'</div><div class="slots">'; cur=s.day; }
      h+='<button data-s="'+s.slot+'">'+s.hm+'</button>';
    });
    h+='</div></div>';
    h+='<button class="go" id="bk">约 这 个 时 间</button>';
  }
  h+='<div class="err" id="err"></div>';
  h+='<div class="hint">约好扣的是余额，<b>没到点前可以退</b>。<br>老师这边确认了才算数。</div>';
  if(D.mine.length){
    h+='<div class="hint" style="margin-top:26px;color:#6d675e">我 约 的</div>';
    D.mine.forEach(function(r){
      var st={booked:'等他确认',done:'已完成',cancel:'已退'}[r.status]||r.status;
      var gone = (r.status === 'done' || r.status === 'cancel');
      var tag = r.token ? '进去 ›' : '';
      h+='<a class="mine" style="text-decoration:none;color:inherit;'+
         (gone?'opacity:.45':'')+'" href="'+(r.token?('/xin/join/'+r.token):'#')+'">'+
         '<div>'+H(r.slot.substr(5,11))+' · '+H(r.label)+
         '<div class="s">'+st+'</div></div>'+
         '<div>￥'+r.amount+(tag?'<div class="s" style="color:#c9a961">'+tag+'</div>':'')+'</div></a>';
    });
  }
  box.innerHTML=h;
  var tabs=document.querySelectorAll('.tab div');
  for(var i=0;i<tabs.length;i++){
    tabs[i].onclick=function(){KIND=this.getAttribute('data-k');PICK='';load();};
  }
  var bt=document.querySelectorAll('.slots button');
  for(var j=0;j<bt.length;j++){
    bt[j].onclick=function(){
      PICK=this.getAttribute('data-s');
      for(var k=0;k<bt.length;k++) bt[k].className=(bt[k]===this?'on':'');
      var gg=document.getElementById('bk');
      if(gg) gg.textContent='约 '+PICK.substr(5,11)+' · ￥'+PRICE[KIND];
    };
  }
  var g=document.getElementById('bk');
  var nw=document.getElementById('now');
  if(nw) nw.onclick=function(e){
    e.preventDefault();
    var tp=(document.getElementById('tpc')||{}).value||'';
    if(!confirm('现在就开始？会马上扣 '+PRICE[KIND]+' 元')){
      return;
    }
    nw.textContent='正在接通…';
    api('/api/live/instant',{kind:KIND,topic:tp}).then(function(j){
      if(j.ok&&j.token){ location.href='/xin/join/'+j.token; return; }
      nw.textContent='他 现 在 在 · 现 在 就 约';
      var e2=document.getElementById('err');
      e2.innerHTML=H(j.msg||'没约上')+(j.need?('<br><a href="/xin/me" style="color:#c9a961">'
        +'去充 '+Math.ceil(j.need)+' 元 ›</a>'):'');
    });
  };
  if(g) g.onclick=function(){
    if(!PICK){document.getElementById('err').textContent='先挑一个时间';return;}
    var b=this; b.disabled=true;
    var tp0=(document.getElementById('tpc')||{}).value||'';
    api('/api/live/book',{slot:PICK,kind:KIND,topic:tp0}).then(function(j){
      b.disabled=false;
      if(!j.ok){
        var e=document.getElementById('err');
        e.innerHTML=H(j.msg||'没约上')+(j.need?('<br><a href="/xin/me" style="color:#c9a961">'
          +'去充 '+Math.ceil(j.need)+' 元 ›</a>'):'');
        return;
      }
      var LINK = location.origin + '/xin/join/' + j.token;
      document.getElementById('box').innerHTML=
        '<div class="ok"><div class="big">约好了</div>'+
        '<div class="t1">'+H(PICK)+'<br>'+(KIND==='voice'?'语音':'视频')+' 20 分钟<br>'+
        '余额还剩 ￥'+j.balance+'</div></div>'+
        '<div class="box"><div style="font-size:12.5px;color:#8d8578;margin-bottom:9px">'+
        '这一场的门，存好它</div>'+
        '<div style="font-size:11.5px;color:#c9a961;word-break:break-all;line-height:1.7;'+
        'background:rgba(201,169,97,.07);padding:10px;border-radius:4px">'+LINK+'</div>'+
        '<button class="ghost" id="cpj" style="margin-top:11px">复制链接</button></div>'+
        '<a class="go" style="display:block;text-align:center;text-decoration:none" '+
        'href="/xin/join/'+j.token+'">现在就进去看看</a>'+
        '<div class="hint" style="text-align:center">到点了从这里进，直接跟他说话<br>'+
        '不想用网页也行 —— 里面也有他的微信</div>'+
        '<a class="ghost" href="/xin/live">再约一个</a>';
      var cb = document.getElementById('cpj');
      cb.onclick = function(){
        var m2=this;
        if(navigator.clipboard && window.isSecureContext){
          navigator.clipboard.writeText(LINK).then(function(){ m2.textContent='复制好了 ✓'; });
        } else {
          var ta=document.createElement('textarea'); ta.value=LINK;
          document.body.appendChild(ta); ta.select();
          try{ document.execCommand('copy'); m2.textContent='复制好了 ✓'; }catch(e){}
          document.body.removeChild(ta);
        }
      };
    }).catch(function(){b.disabled=false;});
  };
}

function load(){
  api('/api/live/state').then(function(D){draw(D);})
   .catch(function(){document.getElementById('box').innerHTML='<div class="hint">读不到，刷新一下</div>';});
}
load();
</script>
"""


# ---------------------------------------------------------------- 后台
OPS_HEAD = ('<!DOCTYPE html><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>body{background:#0a0a0a;color:#ddd6c8;font-family:-apple-system,"PingFang SC",sans-serif;'
            'padding:16px 14px 40px;font-size:14px;line-height:1.7;margin:0}'
            'h1{font-size:18px;color:#f2ede2;letter-spacing:.08em;margin:6px 0 16px}'
            'h2{font-size:13px;color:#c9a961;margin:24px 0 10px;letter-spacing:.06em;font-weight:500}'
            '.i{border-left:2px solid rgba(201,169,97,.55);padding:9px 0 9px 12px;margin-bottom:10px}'
            '.t{font-size:11.5px;color:#6d675e}.s{color:#e8c07a;font-size:14px;letter-spacing:.06em}'
            'button{background:rgba(201,169,97,.14);border:1px solid rgba(201,169,97,.4);color:#c9a961;'
            'font-family:inherit;font-size:11.5px;padding:5px 12px;border-radius:3px;margin:7px 6px 0 0;cursor:pointer}'
            'a{color:#c9a961}</style>'
            '<div style="display:flex;align-items:center;gap:11px;margin:0 0 18px"><img src="/xin/m/avatar-s.png" alt="" style="width:42px;height:42px;border-radius:21px;object-fit:cover;border:1px solid rgba(201,169,97,.4)"><div style="font-size:12.5px;color:#A79C89;letter-spacing:.1em">我的小站</div></div>')


def install(app):
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    @app.get("/xin/live", response_class=HTMLResponse)
    def _live_page():
        return ("<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
                "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
                "<title>约他说话 · 夜话</title><style>" + CSS + "</style></head><body>"
                + BODY + "</body></html>")

    @app.get("/xin/api/live/state")
    def _live_state(req: Request):
        uid = acct.uid_of(req)
        if not uid:
            # 体验模式：不登录也给一个游客身份，能看能走流程
            uid = acct.guest_uid(req)
        if not uid:
            return {"login": 0}
        u = acct.me(uid)
        import shop as _sh
        pp = _sh.prods()
        prices = {}
        for k in ("voice", "video"):
            prices[k] = {"price": _sh._n(pp[k]["price"]), "orig": _sh._n(pp[k]["orig"]),
                         "minutes": pp[k]["minutes"], "on": pp[k]["on"],
                         "label": pp[k]["label"]}
        return {"login": 1, "guest": (1 if is_guest(uid) else 0),
                "balance": round(u["balance"], 2),
                "slots": slots(), "mine": my(uid), "prices": prices,
                "online": boss_online()}

    @app.post("/xin/api/live/instant")
    async def _live_instant(req: Request):
        uid = acct.uid_of(req)
        if not uid:
            return {"ok": 0, "msg": "先登录"}
        d = await req.json()
        kind = (d.get("kind") or "voice").strip()
        if kind not in PRICE:
            return {"ok": 0, "msg": "类型不对"}
        if not boss_online():
            return {"ok": 0, "msg": "他现在不在，还是挑个时间吧"}
        return instantly(uid, kind, d.get("topic") or "")

    @app.post("/xin/api/live/book")
    async def _live_book(req: Request):
        uid = acct.uid_of(req) or acct.guest_uid(req)
        if not uid:
            return {"ok": 0, "msg": "先登录"}
        d = await req.json()
        return book(uid, (d.get("slot") or "").strip(),
                    (d.get("kind") or "voice").strip(), d.get("topic") or "")

    @app.get("/xin/liveops/{key}", response_class=HTMLResponse)
    def _live_ops(key: str):
        if not key or key != core.get("ops_key"):
            return HTMLResponse("<h2>没有入口</h2>", status_code=403)
        c = _c()
        rows = c.execute("""SELECT b.*, u.phone, u.nick FROM booking b
                            LEFT JOIN usr u ON u.id=b.uid
                            ORDER BY b.slot DESC LIMIT 60""").fetchall()
        c.close()
        cf = cfg()
        h = [OPS_HEAD, "<h1>真人预约</h1>",
             '<div class="t">现在排期：每周 %s · %s</div>'
             % ("/".join(str(d) for d in cf["days"]), " / ".join(cf["times"]))]
        now = time.time()
        for r in rows:
            st = r["status"]
            try:
                left = int((time.mktime(_dt(r["slot"])) - now) / 60)
            except Exception:
                left = 0
            tip = {"booked": "等到点", "done": "已完成", "cancel": "已退"}.get(st, st)
            if st == "booked" and 0 <= left <= 30:
                tip = "<span style='color:#e8c07a'>马上就到（还有 %d 分钟）</span>" % left
            h.append('<div class="i"><div class="s">%s · %s</div>'
                     '<div class="t">%s ￥%s · %s · %s</div>'
                     '%s</div>'
                     % (r["slot"], LABEL.get(r["kind"], ""),
                        (r["phone"] or "?") + " " + (r["nick"] or ""), r["amount"], tip,
                        r["created"][5:16],
                        ('<button onclick="st(this,%d,\'done\')">做完了</button>'
                         '<button onclick="st(this,%d,\'cancel\')">退掉</button>'
                         % (r["id"], r["id"])) if st == "booked" else ""))
        h.append('<script>function st(b,id,s){if(!confirm("确定？"))return;'
                 'fetch("/xin/api/live/status",{method:"POST",headers:{"Content-Type":"application/json"},'
                 'body:JSON.stringify({key:"%s",id:id,status:s})}).then(function(r){return r.json();})'
                 '.then(function(j){if(j.ok){b.textContent="已"+s;b.style.color="#8fd39c";}'
                 'else{b.textContent=j.msg||"失败";}});}</script>' % key)
        return "".join(h)

    @app.post("/xin/api/live/status")
    async def _live_status(req: Request):
        d = await req.json()
        if (d.get("key") or "") != core.get("ops_key"):
            return {"ok": 0, "msg": "没有权限"}
        bid = int(d.get("id") or 0)
        st = (d.get("status") or "").strip()
        if st not in ("done", "cancel"):
            return {"ok": 0, "msg": "状态不对"}
        c = _c()
        r = c.execute("SELECT * FROM booking WHERE id=?", (bid,)).fetchone()
        c.close()
        if not r:
            return {"ok": 0, "msg": "没有这单"}
        if r["status"] != "booked":
            return {"ok": 0, "msg": "这单已经处理过"}
        c = _c()
        c.execute("UPDATE booking SET status=?, done_at=? WHERE id=?", (st, core.now(), bid))
        c.commit()
        c.close()
        if st == "cancel":
            acct.ledger_add(r["uid"], round(r["amount"], 2), "refund", "booking:%d" % bid)
        return {"ok": 1}
