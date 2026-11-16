# -*- coding: utf-8 -*-
"""夜话 · 账户 / 余额 / 充值 / 消费流水
挂载：app.py 末尾  import acct; acct.install(APP)
"""
import hashlib
import hmac
import os
import re
import sqlite3
import time

import core
import conf

CHAT_PRICE = 1.0            # 分身每句（元）
LIVE_PRICE = 3.0            # 真人每分钟（元，预约用）
TIERS = [(30, 0), (100, 10), (300, 50)]   # 充值档：（金额，赠送）
LEVELS = [(300, "gold", "金卡"), (100, "silver", "银卡"), (0, "normal", "普通")]


def _c():
    c = sqlite3.connect(core.DB)
    c.row_factory = sqlite3.Row
    return c


def _sec():
    v = core.get("acct_secret")
    if not v:
        v = hashlib.sha256(os.urandom(32)).hexdigest()[:40]
        core.set("acct_secret", v)
    return v


def init():
    c = _c()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS usr (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      phone TEXT UNIQUE,
      pw TEXT,
      nick TEXT DEFAULT '',
      sid TEXT DEFAULT '',
      balance REAL DEFAULT 0,
      total_in REAL DEFAULT 0,
      level TEXT DEFAULT 'normal',
      created TEXT, last TEXT);
    CREATE TABLE IF NOT EXISTS ord (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      uid INTEGER, amount REAL, bonus REAL DEFAULT 0,
      code TEXT UNIQUE, status TEXT DEFAULT 'wait',
      note TEXT DEFAULT '', created TEXT, paid_at TEXT);
    CREATE TABLE IF NOT EXISTS ledger (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      uid INTEGER, delta REAL, reason TEXT, ref TEXT DEFAULT '',
      bal REAL, created TEXT);
    CREATE TABLE IF NOT EXISTS booking (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      uid INTEGER, slot TEXT, kind TEXT DEFAULT 'voice',
      minutes INTEGER DEFAULT 20, amount REAL DEFAULT 0,
      status TEXT DEFAULT 'wait',
      note TEXT DEFAULT '', created TEXT, done_at TEXT);
    """)
    c.commit()
    c.close()
    _sec()


init()


# ---------------------------------------------------------------- 身份
def _hash(pw):
    return hashlib.sha256((_sec() + "|" + pw).encode()).hexdigest()


def make_tok(uid):
    sig = hmac.new(_sec().encode(), str(uid).encode(), hashlib.sha256).hexdigest()[:24]
    return "%d.%s" % (uid, sig)


def parse_tok(tok):
    try:
        a, b = (tok or "").split(".", 1)
        uid = int(a)
        exp = hmac.new(_sec().encode(), str(uid).encode(), hashlib.sha256).hexdigest()[:24]
        return uid if hmac.compare_digest(exp, b) else 0
    except Exception:
        return 0


def uid_of(req):
    try:
        return parse_tok(req.cookies.get("xtok") or "")
    except Exception:
        return 0


def guest_uid(req):
    """体验模式：同一个 IP 给同一个游客身份，不用登录、不用注册。"""
    import hashlib
    try:
        ip = (req.headers.get("x-real-ip") or "").strip()
        if not ip:
            ip = (req.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        if not ip and req.client:
            ip = req.client.host
        h = hashlib.sha256(("guest|" + (ip or "x")).encode()).hexdigest()[:14]
        tag = "g_" + h
        c = _c()
        r = c.execute("SELECT id FROM usr WHERE phone=?", (tag,)).fetchone()
        if r:
            c.close()
            return r["id"]
        c.execute("""INSERT INTO usr(phone,pw,nick,balance,total_in,level,created,last)
                     VALUES(?,?,?,0,0,0,?,?)""",
                  (tag, "-", "来体验的", core.now(), core.now()))
        c.commit()
        nid = c.execute("SELECT id FROM usr WHERE phone=?", (tag,)).fetchone()["id"]
        c.close()
        return nid
    except Exception as e:
        print("[guest]", e)
        return 0


def me(uid):
    c = _c()
    r = c.execute("SELECT * FROM usr WHERE id=?", (uid,)).fetchone()
    c.close()
    return dict(r) if r else None


def lvl(total_in):
    for t, k, n in LEVELS:
        if total_in >= t:
            return k, n
    return "normal", "普通"


# ---------------------------------------------------------------- 钱
def _bal(uid):
    r = me(uid)
    return round(r["balance"], 2) if r else 0.0


def ledger_add(uid, delta, reason, ref=""):
    c = _c()
    c.execute("UPDATE usr SET balance=ROUND(balance+?,2) WHERE id=?", (delta, uid))
    b = c.execute("SELECT balance FROM usr WHERE id=?", (uid,)).fetchone()["balance"]
    c.execute("INSERT INTO ledger(uid,delta,reason,ref,bal,created) VALUES(?,?,?,?,?,?)",
              (uid, delta, reason, ref, b, core.now()))
    c.commit()
    c.close()
    return round(b, 2)


def charge(uid, amount, reason, ref=""):
    """扣费；余额不足返回 (False, 余额)"""
    b = _bal(uid)
    if b < amount:
        return False, b
    return True, ledger_add(uid, -round(amount, 2), reason, ref)


def recharge(uid, amount, bonus, code):
    c = _c()
    c.execute("UPDATE ord SET status='paid', paid_at=? WHERE code=?", (core.now(), code))
    c.execute("UPDATE usr SET total_in=ROUND(total_in+?,2) WHERE id=?", (amount + bonus, uid))
    r = c.execute("SELECT total_in FROM usr WHERE id=?", (uid,)).fetchone()
    k, _n = lvl(r["total_in"])
    c.execute("UPDATE usr SET level=? WHERE id=?", (k, uid))
    c.commit()
    c.close()
    return ledger_add(uid, round(amount + bonus, 2), "recharge", code)


def new_code():
    c = _c()
    for _ in range(20):
        code = "YS%s%03d" % (time.strftime("%m%d"), __import__("random").randint(1, 999))
        if not c.execute("SELECT 1 FROM ord WHERE code=?", (code,)).fetchone():
            c.close()
            return code
    c.close()
    return "YS%s%s" % (time.strftime("%m%d%H%M"), __import__("random").randint(10, 99))


# ---------------------------------------------------------------- 付款提醒
def notify_claim(code, amount, phone, nick, check_only=False):
    """有人点「我付好了」→ 立刻发信（后台线程）"""
    import subprocess
    import threading

    def _m():
        try:
            u = conf.u("/xin/orders/%s") % core.get("ops_key")
            hp = "/tmp/claim_%s.html" % code
            with open(hp, "w", encoding="utf-8") as f:
                f.write(
                    '<div style="font-family:-apple-system,sans-serif;padding:10px">'
                    '<h2 style="font-size:18px;margin:0 0 14px">有人付了钱，等你核对</h2>'
                    '<table cellpadding="8" cellspacing="0" style="font-size:15px;border-collapse:collapse">'
                    '<tr><td style="color:#888;padding-right:18px">订单号</td><td><b>%s</b></td></tr>'
                    '<tr><td style="color:#888">金额</td><td><b style="font-size:19px">￥%s</b></td></tr>'
                    '<tr><td style="color:#888">是谁</td><td>%s %s</td></tr>'
                    '</table>'
                    '<p style="font-size:14px;color:#444;margin-top:16px;line-height:1.9">'
                    '打开微信收款记录，找备注里写着 <b>%s</b> 的那一笔。<br>'
                    '对上了，就去后台点「收到了」。</p>'
                    '<p style="font-size:15px;margin-top:18px">'
                    '<a href="%s" style="background:#111;color:#fff;padding:11px 20px;'
                    'border-radius:6px;text-decoration:none">去核对入账</a></p></div>'
                    % (code, amount, phone, nick or "", code, u))
            subprocess.run([conf.PYBIN, conf.SENDMAIL,
                            "--to", conf.OPS_EMAIL, "--from-name", conf.MAIL_FROM,
                            "--subject", "有人付了 ￥%s（%s）" % (amount, code),
                            "--html", hp],
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
        except Exception:
            pass

    threading.Thread(target=_m, daemon=True).start()


# ---------------------------------------------------------------- 页面
CSS = """
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:#0a0a0a;color:#e8e2d6;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Noto Sans CJK SC",sans-serif;
 line-height:1.8;-webkit-font-smoothing:antialiased;min-height:100vh}
.wrap{max-width:520px;margin:0 auto;padding:34px 22px 60px}
h1{font-family:"Songti SC","Noto Serif CJK SC",serif;font-size:23px;font-weight:600;
 letter-spacing:.1em;color:#f2ede2;margin-bottom:6px}
.sub{font-size:12px;color:#6d675e;letter-spacing:.16em;margin-bottom:28px}
.bal{background:linear-gradient(160deg,rgba(201,169,97,.13),rgba(201,169,97,.04));
 border:1px solid rgba(201,169,97,.25);border-radius:5px;padding:24px 20px;margin-bottom:14px;text-align:center}
.bal .n{font-size:40px;font-weight:300;color:#e8c07a;letter-spacing:.03em;line-height:1.2}
.bal .n i{font-size:16px;font-style:normal;color:#9a9286;margin-right:4px}
.bal .l{font-size:12px;color:#8d8578;letter-spacing:.1em;margin-top:8px}
.tier{display:flex;gap:9px;margin:16px 0 22px}
.tier button{flex:1;background:rgba(255,255,255,.03);border:1px solid rgba(201,169,97,.2);
 color:#b9ad95;border-radius:4px;padding:14px 6px;font-family:inherit;cursor:pointer;transition:.18s}
.tier button:active{background:rgba(201,169,97,.14)}
.tier b{display:block;font-size:19px;color:#e8c07a;font-weight:500;letter-spacing:.02em}
.tier span{display:block;font-size:11px;color:#6d675e;margin-top:4px}
.tier button.on{border-color:#c9a961;background:rgba(201,169,97,.12)}
.in{width:100%;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.09);
 border-radius:4px;color:#e8e2d6;font-family:inherit;font-size:15px;padding:13px 14px;outline:none;margin-bottom:10px}
.in:focus{border-color:rgba(201,169,97,.45)}
.go{width:100%;background:#c9a961;color:#0a0a0a;border:0;border-radius:4px;font-family:inherit;
 font-size:15px;font-weight:600;padding:14px;letter-spacing:.1em;cursor:pointer;margin-top:6px}
.go:disabled{opacity:.4}
.ghost{width:100%;background:transparent;border:1px solid rgba(201,169,97,.3);color:#c9a961;
 border-radius:4px;font-family:inherit;font-size:14px;padding:13px;letter-spacing:.08em;cursor:pointer;margin-top:10px}
.tab{display:flex;gap:0;margin-bottom:20px;border-bottom:1px solid rgba(255,255,255,.08)}
.tab div{flex:1;text-align:center;padding:11px 0;font-size:13.5px;color:#6d675e;letter-spacing:.1em;
 cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px}
.tab div.on{color:#c9a961;border-bottom-color:#c9a961}
.sec{margin:26px 0 12px;font-size:11.5px;color:#6d675e;letter-spacing:.2em}
.lrow{display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px solid rgba(255,255,255,.05);
 font-size:13.5px}
.lrow .t{color:#8d8578;font-size:11.5px;margin-top:2px}
.plus{color:#8fd39c}
.minus{color:#c9a961}
.pay{text-align:center;border:1px solid rgba(201,169,97,.25);border-radius:5px;padding:20px 16px;margin-top:16px}
.pay img{width:190px;height:190px;object-fit:contain;background:#fff;padding:6px;border-radius:4px;margin:10px auto}
.pay .cd{font-size:13px;color:#e8c07a;letter-spacing:.14em;margin:8px 0}
.pay .ph{font-size:11.5px;color:#6d675e;line-height:1.9}
.hint{font-size:12px;color:#6d675e;line-height:1.9;margin-top:14px}
.err{color:#e8a49b;font-size:12.5px;margin-top:10px;min-height:18px}
a{color:#c9a961;text-decoration:none}
"""

BODY = """
<div style="display:flex;align-items:center;gap:11px;margin:0 0 18px"><img src="/xin/m/avatar-s.png" alt="" style="width:42px;height:42px;border-radius:21px;object-fit:cover;border:1px solid rgba(201,169,97,.4)"><div style="font-size:12.5px;color:#A79C89;letter-spacing:.1em">我的小站</div></div>
<div class="wrap">
<div id="box">正在读取…</div>
</div>
<script>
var BASE='/xin';
function H(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){
 return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function api(p,o){
  return fetch(BASE+p,o?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o),
    credentials:'same-origin'}:{credentials:'same-origin'}).then(function(r){return r.json();});
}
function money(n){return (Math.round(n*100)/100).toFixed(2);}
var ME=null, TIER=0;

function render(){
  var box=document.getElementById('box');
  if(!ME || !ME.ok){ box.innerHTML=loginHTML(); bindLogin(); return; }
  box.innerHTML=acctHTML(); bindAcct();
}

function loginHTML(){
  return '<h1>我的</h1><div class="sub">夜 话 · 登 录</div>'+
   '<div class="tab"><div class="on" id="t1">登录</div><div id="t2">注册</div></div>'+
   '<input class="in" id="ph" placeholder="手机号" inputmode="numeric" maxlength="11">'+
   '<input class="in" id="pw" placeholder="密码（6位以上）" type="password">'+
   '<input class="in" id="nk" placeholder="称呼（可不填）" style="display:none">'+
   '<button class="go" id="sub">登 录</button>'+
   '<div class="err" id="err"></div>'+
   '<div class="hint">登录后，充的钱记在账上，换手机也能接着用。<br>'+
   '不想注册也行 —— 回<a href="/xin/chat">夜话</a>，先免费说三句。</div>';
}

function bindLogin(){
  var reg=false;
  document.getElementById('t1').onclick=function(){reg=false;sw();};
  document.getElementById('t2').onclick=function(){reg=true;sw();};
  function sw(){
    document.getElementById('t1').className=reg?'':'on';
    document.getElementById('t2').className=reg?'on':'';
    document.getElementById('nk').style.display=reg?'':'none';
    document.getElementById('sub').textContent=reg?'注 册':'登 录';
    document.getElementById('err').textContent='';
  }
  document.getElementById('sub').onclick=function(){
    var b=this; b.disabled=true;
    var ph=(document.getElementById('ph').value||'').trim();
    var pw=(document.getElementById('pw').value||'').trim();
    var nk=(document.getElementById('nk').value||'').trim();
    api(reg?'/api/me/reg':'/api/me/login',{phone:ph,pw:pw,nick:nk}).then(function(j){
      b.disabled=false;
      if(!j.ok){document.getElementById('err').textContent=j.msg||'没成功';return;}
      load();
    }).catch(function(){b.disabled=false;document.getElementById('err').textContent='网络不好';});
  };
}

function acctHTML(){
  var d=ME, h='';
  h+='<h1>我的</h1><div class="sub">'+H(d.nick||d.phone)+' · '+H(d.level_name)+'</div>';
  h+='<div class="bal"><div class="n"><i>￥</i>'+money(d.balance)+'</div>'+
     '<div class="l">余额 · 分身一句 1 元</div></div>';
  h+='<div class="sec">充 值</div><div class="tier">';
  d.tiers.forEach(function(t,i){
    h+='<button data-i="'+i+'" class="'+(i===0?'on':'')+'"><b>'+t[0]+'</b><span>'+
       (t[1]?'送 '+t[1]+' 元':'充多少用多少')+'</span></button>';
  });
  h+='</div><button class="go" id="rc">充 值</button>';
  h+='<div id="paybox"></div>';
  if(d.pending && d.pending.length){
    h+='<div class="hint" style="color:#e8c07a">还在等他核对：'+
       d.pending.map(function(p){return p.code+' ￥'+p.amount;}).join('　')+'</div>';
  }

  h+='<div class="sec">最 近</div>';
  var ps=d.pending||[];
  for(var pi=0;pi<ps.length;pi++){
    var pp=ps[pi];
    h+='<div class="lrow" style="border-left:2px solid rgba(201,169,97,.55);padding-left:9px;'+
       'background:rgba(201,169,97,.045)"><div>充值 <span style="font-size:11px;color:#c9a961">'+
       (pp.status==='claimed'?'· 等他核对':'· 还没付')+'</span>'+
       '<div class="t">'+H(pp.created)+'</div></div>'+
       '<div style="color:#6d675e">+'+(Math.round((pp.amount+pp.bonus)*100)/100)+'</div></div>';
  }
  if(!d.ledger.length && !ps.length){ h+='<div class="hint">还没有记录。充值后在这里看明细。</div>'; }
  d.ledger.forEach(function(r){
    var cls=r.delta>0?'plus':'minus';
    h+='<div class="lrow"><div>'+H(r.reason_text)+'<div class="t">'+H(r.created.substr(5,11))+'</div></div>'+
       '<div class="'+cls+'">'+(r.delta>0?'+':'')+money(r.delta)+'</div></div>';
  });
  h+='<button class="ghost" id="out">退出登录</button>';
  h+='<div class="hint"><a href="/xin/chat">← 回去说两句</a></div>';
  return h;
}

function bindAcct(){
  var btns=document.querySelectorAll('.tier button');
  for(var i=0;i<btns.length;i++){
    btns[i].onclick=function(){
      var k=parseInt(this.getAttribute('data-i'),10);
      TIER=k;
      for(var j=0;j<btns.length;j++) btns[j].className=(j===k?'on':'');
    };
  }
  document.getElementById('rc').onclick=function(){
    var b=this; b.disabled=true;
    var t=ME.tiers[TIER];
    api('/api/me/recharge',{amount:t[0]}).then(function(j){
      b.disabled=false;
      if(!j.ok){alert(j.msg||'没成功');return;}
      document.getElementById('paybox').innerHTML=
        '<div class="pay">'+
        '<div class="ph">扫码付 '+j.amount+' 元</div>'+
        '<img src="/xin/m/pay.png">'+
        '<div class="ph" style="margin-top:4px">转账的<b>备注</b>里填这串</div>'+
        '<div class="cd" style="font-size:17px">'+j.code+'</div>'+
        '<button class="ghost" id="cp2">复制这串</button>'+
        '<button class="go" id="rc2" style="margin-top:12px">我 付 好 了</button>'+
        '<div class="ph" style="margin-top:12px">点完，老师手机立刻收到提醒<br>他核对完，这里自动变成余额</div>'+
        '</div>';
      document.getElementById('cp2').onclick=function(){
        var t=j.code, me2=this;
        function done(){ me2.textContent='复制好了 ✓'; }
        if(navigator.clipboard && window.isSecureContext){
          navigator.clipboard.writeText(t).then(done).catch(function(){ fb(); });
        } else { fb(); }
        function fb(){
          var ta=document.createElement('textarea'); ta.value=t;
          ta.style.position='fixed'; ta.style.top='-1000px';
          document.body.appendChild(ta); ta.select();
          try{document.execCommand('copy');done();}catch(e){}
          document.body.removeChild(ta);
        }
      };
      document.getElementById('rc2').onclick=function(){
        var bb=this; bb.disabled=true; bb.textContent='已告诉老师了…';
        api('/api/me/claim',{code:j.code}).then(function(x){
          if(!x.ok){bb.disabled=false;bb.textContent='我 付 好 了';
            alert(x.msg||'没提交成功');return;}
          document.getElementById('paybox').innerHTML=
            '<div class="pay"><div style="font-size:16px;color:#e8c07a;letter-spacing:.1em;margin-bottom:10px">'+
            '等老师核对一下</div><div class="ph">订单 '+j.code+'<br>通常一两分钟，最多半小时<br>'+
            '他一确认，余额自己会变<br>别关这个页面</div></div>';
          watch(j.code);
        }).catch(function(){bb.disabled=false;bb.textContent='我 付 好 了';});
      };
    }).catch(function(){b.disabled=false;});
  };
  document.getElementById('out').onclick=function(){
    api('/api/me/out',{}).then(load);
  };
}

var WT=null, WN=0;
function watch(code){
  WN=0;
  if(WT) clearInterval(WT);
  WT=setInterval(function(){
    WN++;
    if(WN>72){ clearInterval(WT); return; }
    api('/api/me/info').then(function(j){
      if(!j.ok) return;
      var still=false;
      var ps=j.pending||[];
      for(var i=0;i<ps.length;i++){ if(ps[i].code===code) still=true; }
      if(!still){
        clearInterval(WT);
        ME=j; render();
        var box=document.getElementById('box');
        if(box){
          var tip=document.createElement('div');
          tip.className='hint';
          tip.style.cssText='color:#8fd39c;font-size:13.5px;margin-top:12px';
          tip.textContent='到账了，余额 ￥'+money(j.balance);
          box.insertBefore(tip,box.firstChild);
        }
      }
    }).catch(function(){});
  },5000);
}

function load(){
  api('/api/me/info').then(function(j){ME=j;render();})
   .catch(function(){document.getElementById('box').innerHTML='<div class="hint">读不到，刷新一下</div>';});
}
load();
</script>
"""


# ---------------------------------------------------------------- 后台页
OPS_HEAD = ('<!DOCTYPE html><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>body{background:#0a0a0a;color:#ddd6c8;font-family:-apple-system,"PingFang SC",sans-serif;'
            'padding:16px 14px 40px;font-size:14px;line-height:1.7;margin:0}'
            'h1{font-size:18px;color:#f2ede2;letter-spacing:.08em;margin:6px 0 16px}'
            'h2{font-size:13px;color:#c9a961;margin:24px 0 10px;letter-spacing:.06em;font-weight:500}'
            '.i{border-left:2px solid rgba(201,169,97,.55);padding:9px 0 9px 12px;margin-bottom:10px}'
            '.t{font-size:11.5px;color:#6d675e}.cd{color:#e8c07a;letter-spacing:.1em;font-size:13px}'
            'button{background:rgba(201,169,97,.14);border:1px solid rgba(201,169,97,.4);color:#c9a961;'
            'font-family:inherit;font-size:11.5px;padding:5px 12px;border-radius:3px;margin-top:7px;cursor:pointer}'
            'a{color:#c9a961}</style>'
            '<div style="display:flex;align-items:center;gap:11px;margin:0 0 18px"><img src="/xin/m/avatar-s.png" alt="" style="width:42px;height:42px;border-radius:21px;object-fit:cover;border:1px solid rgba(201,169,97,.4)"><div style="font-size:12.5px;color:#A79C89;letter-spacing:.1em">我的小站</div></div>')


# ---------------------------------------------------------------- 路由
def install(app):
    from fastapi import Request
    from fastapi.responses import HTMLResponse, JSONResponse

    @app.get("/xin/me", response_class=HTMLResponse)
    def _me_page():
        return ("<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
                "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
                "<title>我的 · 夜话</title><style>" + CSS + "</style></head><body>"
                + BODY + "</body></html>")

    @app.post("/xin/api/me/reg")
    async def _reg(req: Request):
        d = await req.json()
        ph = re.sub(r"\D", "", d.get("phone") or "")
        pw = (d.get("pw") or "").strip()
        nk = (d.get("nick") or "").strip()[:16]
        if len(ph) != 11:
            return {"ok": 0, "msg": "手机号填 11 位"}
        if len(pw) < 6:
            return {"ok": 0, "msg": "密码最少 6 位"}
        c = _c()
        if c.execute("SELECT 1 FROM usr WHERE phone=?", (ph,)).fetchone():
            c.close()
            return {"ok": 0, "msg": "这个号注册过了，直接登录"}
        c.execute("INSERT INTO usr(phone,pw,nick,created,last) VALUES(?,?,?,?,?)",
                  (ph, _hash(pw), nk or ("用户" + ph[-4:]), core.now(), core.now()))
        c.commit()
        uid = c.execute("SELECT id FROM usr WHERE phone=?", (ph,)).fetchone()["id"]
        c.close()
        r = JSONResponse({"ok": 1})
        r.set_cookie("xtok", make_tok(uid), max_age=86400 * 180,
                     httponly=True, samesite="lax", secure=True)
        return r

    @app.post("/xin/api/me/login")
    async def _login(req: Request):
        d = await req.json()
        ph = re.sub(r"\D", "", d.get("phone") or "")
        pw = (d.get("pw") or "").strip()
        c = _c()
        r = c.execute("SELECT * FROM usr WHERE phone=?", (ph,)).fetchone()
        if not r:
            c.close()
            return {"ok": 0, "msg": "没有这个号，先注册"}
        if r["pw"] != _hash(pw):
            c.close()
            return {"ok": 0, "msg": "密码不对"}
        c.execute("UPDATE usr SET last=? WHERE id=?", (core.now(), r["id"]))
        c.commit()
        c.close()
        j = JSONResponse({"ok": 1})
        j.set_cookie("xtok", make_tok(r["id"]), max_age=86400 * 180,
                     httponly=True, samesite="lax", secure=True)
        return j

    @app.post("/xin/api/me/out")
    def _out():
        j = JSONResponse({"ok": 1})
        j.delete_cookie("xtok")
        return j

    @app.get("/xin/api/me/info")
    def _info(req: Request):
        uid = uid_of(req)
        if not uid:
            return {"ok": 0}
        u = me(uid)
        if not u:
            return {"ok": 0}
        c = _c()
        rows = c.execute("SELECT * FROM ledger WHERE uid=? ORDER BY id DESC LIMIT 25",
                         (uid,)).fetchall()
        c.close()
        NAME = {"recharge": "充值", "chat": "夜话", "live": "真人夜话"}
        led = []
        for r in rows:
            led.append({"delta": r["delta"],
                        "reason_text": NAME.get(r["reason"], r["reason"]),
                        "created": r["created"]})
        _k, ln = lvl(u["total_in"] or 0)
        c = _c()
        pend = c.execute("SELECT code,amount,bonus,status,created FROM ord"
                         " WHERE uid=? AND status IN ('wait','claimed')"
                         " ORDER BY id DESC LIMIT 3", (uid,)).fetchall()
        c.close()
        pends = [{"code": r["code"], "amount": r["amount"], "bonus": r["bonus"],
                  "status": r["status"], "created": r["created"][5:16]} for r in pend]
        return {"ok": 1, "uid": uid, "phone": u["phone"][:3] + "****" + u["phone"][-4:],
                "nick": u["nick"], "balance": round(u["balance"], 2),
                "level": u["level"], "level_name": ln,
                "tiers": TIERS, "ledger": led, "pending": pends}

    @app.post("/xin/api/me/recharge")
    async def _recharge(req: Request):
        uid = uid_of(req)
        if not uid:
            return {"ok": 0, "msg": "先登录"}
        d = await req.json()
        try:
            amount = float(d.get("amount") or 0)
        except Exception:
            amount = 0
        if amount <= 0 or amount > 5000:
            return {"ok": 0, "msg": "金额不对"}
        bonus = 0.0
        for a, b in TIERS:
            if abs(a - amount) < 0.01:
                bonus = float(b)
        code = new_code()
        c = _c()
        c.execute("INSERT INTO ord(uid,amount,bonus,code,status,created) VALUES(?,?,?,?,?,?)",
                  (uid, amount, bonus, code, "wait", core.now()))
        c.commit()
        c.close()
        return {"ok": 1, "code": code, "amount": amount, "bonus": bonus}

    @app.post("/xin/api/me/claim")
    async def _claim(req: Request):
        uid = uid_of(req)
        if not uid:
            return {"ok": 0, "msg": "先登录"}
        d = await req.json()
        code = (d.get("code") or "").strip()
        c = _c()
        r = c.execute("SELECT * FROM ord WHERE code=? AND uid=?", (code, uid)).fetchone()
        if not r:
            c.close()
            return {"ok": 0, "msg": "没这单"}
        if r["status"] == "paid":
            c.close()
            return {"ok": 1, "status": "paid"}
        if r["status"] == "wait":
            c.execute("UPDATE ord SET status='claimed' WHERE code=?", (code,))
            c.commit()
            u = c.execute("SELECT phone,nick FROM usr WHERE id=?", (uid,)).fetchone()
            c.close()
            notify_claim(code, r["amount"], (u["phone"] or "")[:3] + "****" + (u["phone"] or "")[-4:],
                         u["nick"] or "")
            return {"ok": 1, "status": "claimed"}
        c.close()
        return {"ok": 1, "status": r["status"]}

    @app.get("/xin/pay/{key}", response_class=HTMLResponse)
    def _simple_pay(key: str):
        """老师专用：一屏一个「收到了」"""
        if not key or key != core.get("ops_key"):
            return HTMLResponse("<h2>没有入口</h2>", status_code=403)
        c = _c()
        claim = c.execute("""SELECT o.*, u.phone, u.nick FROM ord o
                            LEFT JOIN usr u ON u.id=o.uid
                            WHERE o.status='claimed' ORDER BY o.id DESC LIMIT 10""").fetchall()
        today = c.execute("SELECT COUNT(*) n, SUM(amount) s FROM ord WHERE status='paid'"
                          " AND paid_at LIKE ?", (time.strftime("%Y-%m-%d") + "%",)).fetchone()
        c.close()
        h = ['<!DOCTYPE html><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             '<style>*{margin:0;padding:0;box-sizing:border-box}',
             'body{background:#0a0a0a;color:#e8e2d6;font-family:-apple-system,"PingFang SC",sans-serif;',
             'padding:26px 18px 50px;line-height:1.8}',
             'h1{font-size:19px;color:#f2ede2;letter-spacing:.06em;margin-bottom:6px}',
             '.sub{font-size:12.5px;color:#6d675e;margin-bottom:26px}',
             '.card{border:1px solid rgba(201,169,97,.35);background:rgba(201,169,97,.06);',
             'border-radius:8px;padding:22px 18px;margin-bottom:18px;text-align:center}',
             '.amt{font-size:38px;color:#e8c07a;font-weight:300;letter-spacing:.02em}',
             '.code{font-size:15px;color:#c9a961;letter-spacing:.16em;margin:8px 0 4px}',
             '.who{font-size:12.5px;color:#8d8578;margin-bottom:18px}',
             '.ask{font-size:14px;color:#b9ad95;line-height:1.9;margin-bottom:18px}',
             'button{width:100%;font-family:inherit;font-size:17px;padding:16px;border-radius:6px;',
             'border:0;font-weight:600;letter-spacing:.1em;cursor:pointer;margin-bottom:10px}',
             '.yes{background:#c9a961;color:#0a0a0a}',
             '.no{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.3);color:#b9ad95;',
             'font-size:14px;font-weight:400;padding:12px}',
             '.empty{font-size:14px;color:#6d675e;text-align:center;padding:60px 0;line-height:2.1}',
             '.tk{text-align:center;font-size:12.5px;color:#7d766a;margin-top:30px}',
             '</style>',
             '<div style="display:flex;align-items:center;gap:11px;margin:0 0 18px"><img src="/xin/m/avatar-s.png" alt="" style="width:42px;height:42px;border-radius:21px;object-fit:cover;border:1px solid rgba(201,169,97,.4)"><div style="font-size:12.5px;color:#A79C89;letter-spacing:.1em">我的小站</div></div>',
             '<h1>收到了吗</h1>',
             '<div class="sub">今天 %d 笔钱，共 %s 元</div>'
             % (today["n"] or 0, ("%.0f" % (today["s"] or 0)))]
        # ---- 画的订单（在 art_ord 表，跟充值不在一张表）----
        _art = []
        try:
            import art as _A
            _ac = _A._db()
            _art = _ac.execute(
                "SELECT * FROM art_ord WHERE status='claimed' ORDER BY id DESC LIMIT 30"
            ).fetchall()
            _ac.close()
        except Exception as _e:
            print("[pay art]", _e)

        if _art:
            h.append('<h2>画的订单（%d）</h2>' % len(_art))
            for r in _art:
                h.append('<div class="card"><div class="amt">￥%s</div>'
                         '<div style="font-size:15px;color:#e8e0d0;margin-bottom:6px">'
                         '<b>%s</b></div>'
                         '<div style="font-size:13px;color:#a79e8b;line-height:1.9">'
                         '%s　%s<br>%s<br><span style="color:#6d675e">%s</span></div>'
                         '<button class="yes" onclick="ay(this,%d)">收 到 了</button>'
                         '<button class="no" onclick="ad(this,%d)">不 要 了</button></div>'
                         % (_A.money(r["price"]), r["name"],
                            r["who"] or "有人", r["contact"] or "没留联系",
                            r["note"] or "", (r["created"] or "")[:16],
                            r["id"], r["id"]))
            h.append('<script>'
                     'function _ao(id,st,el){el.disabled=true;el.textContent="...";'
                     'fetch("/xin/api/art/ord",{method:"POST",'
                     'headers:{"Content-Type":"application/json"},'
                     'body:JSON.stringify({key:"' + key + '",id:id,status:st})})'
                     '.then(function(r){return r.json()}).then(function(j){'
                     'if(j.ok){location.reload()}else{el.disabled=false;'
                     'el.textContent="再试"}}).catch(function(){el.disabled=false;'
                     'el.textContent="再试"})}'
                     'function ay(el,id){_ao(id,"done",el)}'
                     'function ad(el,id){if(!confirm("这一单不要了？"))return;_ao(id,"drop",el)}'
                     '</script>')

        if not claim and not _art:
            h.append('<div class="empty">现在没有要确认的。<br>'
                     '有人点了「我付好了」，这里会响一声。</div>')
        for r in claim:
            h.append('<div class="card"><div class="amt">￥%s</div>'
                     '<div class="code">%s</div>'
                     '<div class="who">%s %s</div>'
                     '<div class="ask">打开微信，看看有没有收到 %s 元<br>'
                     '写着 <b style="color:#e8c07a;letter-spacing:.1em">%s</b> 这几个字的，就是这一笔</div>'
                     '<button class="yes" onclick="yn(this,\'%s\',1)">收 到 了</button>'
                     '<button class="no" onclick="yn(this,\'%s\',0)">还没收到</button></div>'
                     % (("%.0f" % r["amount"]) if r["amount"] == int(r["amount"]) else r["amount"],
                        r["code"], (r["nick"] or ""), (r["phone"] or ""),
                        ("%.0f" % r["amount"]), r["code"], r["code"], r["code"]))
        h.append('<script>function yn(b,code,y){'
                 'if(!y){alert("那你让他核对一下，或者等一下再看。\\n先别点收到了。");return;}'
                 'b.disabled=true;b.textContent="入账中…";'
                 'fetch("/xin/api/me/confirm",{method:"POST",headers:{"Content-Type":"application/json"},'
                 'body:JSON.stringify({key:"%s",code:code})}).then(function(r){return r.json();})'
                 '.then(function(j){if(j.ok){document.body.innerHTML='
                 '"<div class=\\"empty\\" style=\\"color:#8fd39c\\">入账了 · 余额 "+j.balance+'
                 '"<br><br>可以退出了</div>";}'
                 'else{b.disabled=false;b.textContent="收 到 了";alert(j.msg||"失败");}});}</script>' % key)
        try:
            import json as _j2
            _lc = _j2.loads(core.get("last_confirm") or "{}")
            if _lc.get("code") and (time.time() - float(_lc.get("ts") or 0)) < 600:
                h.append('<div style="margin-top:22px;padding:14px;border-radius:10px;'
                         'background:rgba(201,169,97,.08);font-size:13.5px;color:#b9ad95">'
                         '刚刚确认了 <b style="color:#e8c07a">%s</b> 的这一笔<br>'
                         '<a href="javascript:undo()" style="color:#e8a07a">点错了，撤回这一笔</a>'
                         '<span style="color:#6d675e">（十分钟内有效）</span></div>'
                         % ((_lc.get("nick") or "") or "一位"))
                h.append('<script>function undo(){'
                         'if(!confirm("把这笔退回去？"))return;'
                         'fetch("/xin/api/me/undo",{method:"POST",'
                         'headers:{"Content-Type":"application/json"},'
                         'body:JSON.stringify({key:"%s"})}).then(function(r){return r.json();})'
                         '.then(function(j){alert(j.ok?("已经撤回，余额回到 "+j.balance):(j.msg||"没撤成"));'
                         'if(j.ok)location.reload();});}</script>' % key)
        except Exception:
            pass
        h.append('<div class="tk">这一页只用来确认钱 · 别发给别人</div>')
        return "".join(h)

    @app.post("/xin/api/me/undo")
    async def _undo(req: Request):
        """十秒内点错了，撤回这一笔"""
        d = await req.json()
        if (d.get("key") or "") != core.get("ops_key"):
            return {"ok": 0, "msg": "没有权限"}
        try:
            import json as _j
            lc = _j.loads(core.get("last_confirm") or "{}")
        except Exception:
            lc = {}
        if not lc or not lc.get("code"):
            return {"ok": 0, "msg": "没有可以撤的"}
        if time.time() - float(lc.get("ts") or 0) > 600:
            return {"ok": 0, "msg": "超过十分钟了，撤不回"}
        c = _c()
        okc, nb = charge(lc["uid"], float(lc["back"]), "undo", lc["code"])
        if not okc:
            c.close()
            return {"ok": 0, "msg": "钱已经花出去了，撤不回"}
        c.execute("UPDATE ord SET status='claimed', paid_at='' WHERE code=?", (lc["code"],))
        c.commit()
        c.close()
        core.set("last_confirm", "")
        return {"ok": 1, "balance": nb, "nick": lc.get("nick") or ""}

    @app.get("/xin/orders/{key}", response_class=HTMLResponse)
    def _orders(key: str):
        if not key or key != core.get("ops_key"):
            return HTMLResponse("<h2>没有入口</h2>", status_code=403)
        c = _c()
        claim = c.execute("""SELECT o.*, u.phone, u.nick FROM ord o
                            LEFT JOIN usr u ON u.id=o.uid
                            WHERE o.status='claimed' ORDER BY o.id DESC LIMIT 50""").fetchall()
        wait = c.execute("""SELECT o.*, u.phone, u.nick FROM ord o
                            LEFT JOIN usr u ON u.id=o.uid
                            WHERE o.status='wait' ORDER BY o.id DESC LIMIT 50""").fetchall()
        done = c.execute("""SELECT o.*, u.phone FROM ord o LEFT JOIN usr u ON u.id=o.uid
                            WHERE o.status='paid' ORDER BY o.id DESC LIMIT 30""").fetchall()
        tot = c.execute("SELECT COUNT(*) n, SUM(balance) b FROM usr").fetchone()
        n_usr = tot["n"] or 0
        pool = round(tot["b"] or 0, 2)
        c.close()
        h = [OPS_HEAD, "<h1>充值确认</h1>",
             '<div class="t">%d 个用户 · 账上余额合计 %.0f 元（这是欠的，不是收入）</div>'
             % (n_usr, pool)]
        h.append('<h2>说付了，等核对（%d）</h2>' % len(claim))
        if not claim:
            h.append('<div class="t">没有。有人点「我付好了」，会出现在这里。</div>')
        for r in claim:
            h.append('<div class="i"><div class="cd">%s</div>'
                     '<div class="t">￥%s%s · %s · %s</div>'
                     '<div class="t">打开微信收款记录，找备注写 %s 的那一笔</div>'
                     '<button onclick="ok(this,\'%s\')">收到了，入账</button></div>'
                     % (r["code"], r["amount"],
                        ("（送 %s）" % r["bonus"]) if r["bonus"] else "",
                        (r["phone"] or "?") + " " + (r["nick"] or ""),
                        r["created"][5:16], r["code"], r["code"]))

        if wait:
            h.append('<h2>下了单还没说付款（%d）</h2>' % len(wait))
            for r in wait:
                h.append('<div class="i"><div class="cd">%s</div>'
                         '<div class="t">￥%s · %s · %s</div></div>'
                         % (r["code"], r["amount"],
                            (r["phone"] or "?") + " " + (r["nick"] or ""),
                            r["created"][5:16]))
        h.append('<h2>已入账（%d）</h2>' % len(done))
        for r in done:
            h.append('<div class="i"><div class="t"><span class="cd">%s</span> · ￥%s · %s · %s</div></div>'
                     % (r["code"], r["amount"], (r["phone"] or ""), (r["paid_at"] or "")[5:16]))
        h.append('<script>function ok(b,code){if(!confirm("确认这笔钱到账了？"))return;'
                 'fetch("/xin/api/me/confirm",{method:"POST",headers:{"Content-Type":"application/json"},'
                 'body:JSON.stringify({key:"%s",code:code})}).then(function(r){return r.json();})'
                 '.then(function(j){if(j.ok){b.textContent="已入账 "+j.balance;b.style.color="#8fd39c";}'
                 'else{b.textContent=j.msg||"失败";}});}</script>' % key)
        return "".join(h)

    @app.post("/xin/api/me/confirm")
    async def _confirm(req: Request):
        d = await req.json()
        if (d.get("key") or "") != core.get("ops_key"):
            return {"ok": 0, "msg": "没有权限"}
        code = (d.get("code") or "").strip()
        c = _c()
        r = c.execute("""SELECT o.*, u.nick FROM ord o LEFT JOIN usr u ON u.id=o.uid
                         WHERE o.code=?""", (code,)).fetchone()
        c.close()
        if not r:
            return {"ok": 0, "msg": "没这单"}
        if r["status"] == "paid":
            return {"ok": 0, "msg": "已经入过账了"}
        b = recharge(r["uid"], r["amount"], r["bonus"] or 0, code)
        try:
            import json as _j
            core.set("last_confirm", _j.dumps({
                "code": code, "uid": r["uid"],
                "back": round(float(r["amount"]) + float(r["bonus"] or 0), 2),
                "nick": (r["nick"] or ""), "ts": time.time()}, ensure_ascii=False))
        except Exception as _e:
            print("[last_confirm]", _e)
        return {"ok": 1, "balance": b}
