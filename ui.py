# -*- coding: utf-8 -*-
"""小站的信 · 页面模板（@@KEY@@ 占位，不用 % / format）"""

# ============================================================ 公共
BASE_CSS = """
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent;-webkit-text-size-adjust:100%}
body{margin:0;line-height:1.7}
img{max-width:100%}
"""

# ============================================================ 收件页（黑金）
XIN_CSS = """
:root{--ink:#0a0d0c;--panel:#121715;--line:rgba(226,196,150,.20);--gold:#e2c496;--txt:#eae6df;--dim:#918d85}
body{background:var(--ink);color:var(--txt);
 font-family:-apple-system,"PingFang SC","Noto Sans CJK SC",sans-serif;
 min-height:100vh;padding:56px 22px 90px}
.serif{font-family:"Songti SC","Noto Serif CJK SC",serif}
.wrap{max-width:520px;margin:0 auto}
.mark{width:80px;height:80px;border-radius:50%;display:block;margin:0 auto 26px;
 object-fit:cover;box-shadow:0 0 0 1px rgba(226,196,150,.22)}
.brand{text-align:center;font-size:13px;letter-spacing:.42em;color:var(--gold);
 text-transform:uppercase;margin-bottom:34px;opacity:.85}
.hero{text-align:center;margin-bottom:42px}
.hero h1{font-size:27px;line-height:1.85;font-weight:500;letter-spacing:.06em;margin:0 0 16px}
.hero p{font-size:14px;color:var(--dim);letter-spacing:.12em;margin:0}
.pick{display:block;width:100%;text-align:left;background:var(--panel);
 border:1px solid var(--line);border-radius:14px;padding:20px 20px 18px;
 margin-bottom:12px;color:var(--txt);cursor:pointer;transition:.2s;font-family:inherit}
.pick:active{transform:scale(.985)}
.pick .top{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
.pick .nm{font-size:18px;letter-spacing:.08em}
.pick .pr{font-size:15px;color:var(--gold);white-space:nowrap}
.pick .ds{font-size:13px;color:var(--dim);margin-top:7px;letter-spacing:.05em;line-height:1.7}
.pick.on{border-color:var(--gold);background:rgba(226,196,150,.07)}

form{margin-top:26px;display:none}
form.show{display:block;animation:fade .35s ease}
@keyframes fade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.lbl{font-size:12.5px;letter-spacing:.16em;color:var(--dim);margin:0 0 10px}
.lbl em{font-style:normal;color:var(--gold)}
textarea,input[type=text],input[type=tel]{
 width:100%;background:#0d1210;border:1px solid var(--line);border-radius:12px;
 color:var(--txt);font-family:inherit;font-size:16px;line-height:1.85;
 padding:15px 15px;outline:none;transition:.2s}
textarea{min-height:170px;resize:vertical}
textarea:focus,input:focus{border-color:rgba(226,196,150,.55)}
.row{margin-bottom:22px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{font-size:13.5px;border:1px solid var(--line);border-radius:20px;
 padding:8px 15px;color:var(--dim);cursor:pointer;transition:.15s;background:transparent;
 font-family:inherit}
.chip.on{border-color:var(--gold);color:var(--gold);background:rgba(226,196,150,.09)}
.submit{width:100%;background:var(--gold);color:#1a1206;border:0;border-radius:12px;
 font-size:17px;font-weight:600;letter-spacing:.2em;padding:17px;cursor:pointer;
 font-family:inherit;margin-top:6px}
.submit:disabled{opacity:.45}
.tip{font-size:12.5px;color:var(--dim);line-height:1.9;margin:14px 0 0;letter-spacing:.04em}
.count{font-size:12.5px;color:var(--gold);text-align:right;margin:6px 0 0}
.done{text-align:center;padding:50px 0 30px;display:none}
.done.show{display:block;animation:fade .5s ease}
.done .ic{width:58px;height:58px;border-radius:50%;border:1px solid var(--gold);
 color:var(--gold);display:flex;align-items:center;justify-content:center;
 margin:0 auto 26px;font-size:24px}
.done h2{font-size:21px;font-weight:500;letter-spacing:.08em;margin:0 0 14px}
.done p{font-size:14px;color:var(--dim);line-height:2;margin:0 auto;max-width:330px}
.pay{margin-top:32px;padding-top:26px;border-top:1px solid var(--line)}
.amt{font-size:42px;color:var(--gold);font-family:"Songti SC","Noto Serif CJK SC",serif;
 line-height:1.2;letter-spacing:.04em}
.paytip{font-size:13.5px;color:var(--dim);margin:12px 0 16px;letter-spacing:.06em}
.qr{width:196px;height:196px;border-radius:10px;display:block;margin:0 auto;
 background:#fff;padding:7px;object-fit:contain}
.paytip2{font-size:13px;color:var(--dim);line-height:1.95;margin:18px 0 0;letter-spacing:.04em}
.hot{border:1px solid rgba(162,80,63,.6);background:rgba(162,80,63,.10);
 border-radius:12px;padding:18px 18px;font-size:14px;line-height:1.95;color:#e8c9c2;
 margin-top:24px;display:none}
.hot.show{display:block}
.hot b{color:#f0a99a}
.foot{text-align:center;font-size:11.5px;color:#5f5b55;line-height:2;margin-top:56px;letter-spacing:.06em}
"""

XIN_HTML = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>@@BRAND@@ · 写信</title><style>@@CSS@@</style></head><body>
<div class="wrap">

  <img class="mark" src="m/avatar.png" alt="">
  <div class="brand">@@BRAND@@</div>

  <div class="hero">
    <h1 class="serif">@@SUB1@@<br>@@SUB2@@</h1>
    <p>@@SUB3@@</p>
  </div>

  <div id="picks">
    <button class="pick" data-k="reply" onclick="pick('reply')">
      <div class="top"><span class="nm serif">回一封信</span><span class="pr">￥@@P_REPLY@@</span></div>
      <div class="ds">你把话说给我听。我亲手写一封，再念给你。<br>四十八小时内回给你。</div>
    </button>
    <button class="pick" data-k="read" onclick="pick('read')">
      <div class="top"><span class="nm serif">代读一段</span><span class="pr">￥@@P_R1@@ 起</span></div>
      <div class="ds">文字你写好，我用我的声音念出来。<br>生日、告白、旁白都可以。</div>
    </button>
  </div>

  <form id="f" onsubmit="return false">
    <div class="row" id="row-note">
      <p class="lbl">你想说的 <em>· 只有我看到</em></p>
      <textarea id="note" placeholder="怎么说都行。可以很长，也可以只有一句。"></textarea>
      <p class="tip" style="margin-top:12px">想到哪写到哪，不用整理。写不下来，就写一句也好。</p>
    </div>

    <div class="row" id="row-tier" style="display:none">
      <p class="lbl">要多长</p>
      <div class="chips" id="tiers">
        <button type="button" class="chip" data-t="r1" onclick="tier('r1')">100 字内 ￥@@P_R1@@</button>
        <button type="button" class="chip" data-t="r2" onclick="tier('r2')">300 字内 ￥@@P_R2@@</button>
        <button type="button" class="chip" data-t="r3" onclick="tier('r3')">600 字内 ￥@@P_R3@@</button>
      </div>
    </div>

    <div class="row" id="row-tone" style="display:none">
      <p class="lbl">想要什么感觉</p>
      <div class="chips" id="tones">
        <button type="button" class="chip on" data-v="温和" onclick="tone(this)">温和</button>
        <button type="button" class="chip" data-v="低沉" onclick="tone(this)">低沉</button>
        <button type="button" class="chip" data-v="明亮" onclick="tone(this)">明亮</button>
        <button type="button" class="chip" data-v="像平常说话" onclick="tone(this)">像平常说话</button>
      </div>
    </div>

    <div class="row">
      <p class="lbl">怎么称呼你 <em>· 可以不填</em></p>
      <input type="text" id="nick" placeholder="名字或昵称">
    </div>
    <div class="row">
      <p class="lbl">怎么联系你 <em>· 可以不填</em></p>
      <input type="text" id="contact" placeholder="微信或手机号">
    </div>

    <button class="submit" id="go" onclick="send()">写好了</button>
    <p class="tip">付钱在微信里，他收到会回你。<br>这里不留你的钱，也不查你的身份。</p>
  </form>

  <div class="done" id="done">
    <div class="ic">✓</div>
    <h2 class="serif">写好了</h2>
    <p id="doneTxt">只有他会看到。</p>

    <div class="pay" id="pay" style="display:none">
      <div class="amt serif" id="payAmt">￥99</div>
      <p class="paytip" style="font-size:14.5px;line-height:2">
        <b>第一步</b>　用手指按住下面这张图，选「保存图片」<br>
        <b>第二步</b>　打开微信 → 右上角 ➕ → 扫一扫 → 右上角相册 → 选刚存的图<br>
        <b>第三步</b>　付完回来，点下面那个按钮
      </p>
      <img class="qr" id="payqr" src="/xin/m/pay.png?v=0" alt=""
        onerror="this.style.display='none';document.getElementById('payno').style.display='block'">
      <div id="payno" style="display:none" class="paytip">（收款码还没设好，直接微信转给他也一样）</div>
      <button class="submit" id="paid" onclick="ipaid()"
        style="margin-top:18px;background:#8A6E4B">我 已 经 付 好 了</button>
      <p class="tip" id="paidTip" style="margin-top:10px">点完他会立刻收到提醒，
        收下钱才开始写。一般一天内。</p>
    </div>
  </div>

  <div class="hot" id="hot">
    <b>先看这一句：</b><br>
    你说的这些，我看到了。但这件事我帮不了你——你需要的是专业的人，不是我。<br>
    打 <b>12356</b>（心理援助热线），或者直接去医院。<br>别一个人扛。
  </div>

  <div class="foot">些微的声音，也值得有人听见<br>@@FOOT@@</div>
</div>


<script>
var KIND='', TIER='', TONE='温和';
function pick(k){
  KIND=k;
  document.querySelectorAll('.pick').forEach(function(b){b.classList.toggle('on', b.dataset.k===k)});
  var f=document.getElementById('f'); f.classList.add('show');
  document.getElementById('row-tier').style.display = (k==='read')?'block':'none';
  document.getElementById('row-tone').style.display = (k==='read')?'block':'none';
  document.getElementById('note').placeholder = (k==='read')
    ? '把要读的文字贴进来。'
    : '怎么说都行。可以很长，也可以只有一句。';
  if(k==='read'&&!TIER) tier('r2');
  setTimeout(function(){document.getElementById('f').scrollIntoView({behavior:'smooth',block:'start'})},80);
}
function tier(t){
  TIER=t;
  document.querySelectorAll('#tiers .chip').forEach(function(b){b.classList.toggle('on', b.dataset.t===t)});
}
function tone(el){
  TONE=el.dataset.v;
  document.querySelectorAll('#tones .chip').forEach(function(b){b.classList.remove('on')});
  el.classList.add('on');
}

function ipaid(){
  var b=document.getElementById('paid');
  if(!window.__tok){ b.textContent='等等，还没送出去'; return; }
  b.disabled=true; b.textContent='正在告诉他…';
  fetch('api/thread/claim', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({tok: window.__tok})})
  .then(function(r){return r.json()}).then(function(j){
    if(j.ok){
      b.textContent='已 经 告 诉 他 了';
      document.getElementById('paidTip').innerHTML=
        '<b style="color:#8A6E4B">他那边已经在响了。</b><br>'
        +'收下钱就开始写，写好会发到你留的联系方式。';
    } else { b.disabled=false; b.textContent='再点一次'; }
  });
}

function send(){
  var note=document.getElementById('note').value.trim();
  if(!note){ alert('还没写呢'); return; }
  if(KIND==='read' && note.length<10){ alert('文字太短了'); return; }
  var b=document.getElementById('go'); b.disabled=true; b.textContent='正在送出去…';
  fetch('api/in', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({kind:KIND, note:note, audio:'', tier:TIER, tone:TONE,
      nick:document.getElementById('nick').value.trim(),
      contact:document.getElementById('contact').value.trim()})
  }).then(function(r){return r.json()}).then(function(j){
    if(!j.ok){ b.disabled=false; b.textContent='再试一次'; alert(j.msg||'没送出去'); return; }
    document.getElementById('f').classList.remove('show');
    document.getElementById('picks').style.display='none';
    document.querySelector('.hero').style.display='none';
    document.getElementById('done').classList.add('show');
    if(j.tok){ window.__tok = j.tok; }
    if(j.warn){
      document.getElementById('doneTxt').innerHTML =
        '只有他会看到。<br><span style="color:#A2503F">这段话里有几处需要留意，'
        + '他会特别当心。</span>';
    }
    if(j.price){
      document.getElementById('payAmt').textContent='￥'+j.price;
      document.getElementById('pay').style.display='block';
    }
    if(j.crisis){ document.getElementById('hot').classList.add('show'); }
  }).catch(function(){ b.disabled=false; b.textContent='再试一次'; alert('网络不好，再点一次'); });
}
</script></body></html>"""


def xin_page(cfg):
    h = XIN_HTML
    for k, v in cfg.items():
        h = h.replace("@@" + k + "@@", str(v))
    return h


# ============================================================ 工作台（米白大字）
DESK_CSS = """
:root{--paper:#FBFAF7;--ink:#23201C;--ink2:#4A443C;--dim:#8C8478;--line:#E6E0D4;--gold:#8A6E4B;--seal:#A2503F}
body{background:var(--paper);color:var(--ink);
 font-family:-apple-system,"PingFang SC","Noto Sans CJK SC",sans-serif;font-size:17px;
 padding:0 0 60px}
.serif{font-family:"Songti SC","Noto Serif CJK SC",serif}
.wrap{max-width:600px;margin:0 auto;padding:0 18px}
header{padding:22px 0 16px;display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--line)}
.logo{width:44px;height:44px;border-radius:50%;flex:0 0 auto;object-fit:cover;
 box-shadow:0 0 0 1px rgba(138,110,75,.28)}
.brand{font-size:16.5px;letter-spacing:.06em;white-space:nowrap}
.brand small{display:block;font-size:10.5px;color:var(--dim);letter-spacing:.2em;margin-top:2px}
.stat{margin-left:auto;text-align:right;font-size:13px;color:var(--dim);line-height:1.5}
.stat b{display:block;font-size:19px;color:var(--gold);font-weight:600}
.sec{margin:28px 0 12px;font-size:14.5px;letter-spacing:.16em;color:var(--dim)}
.item{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;
 background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 16px;
 margin-bottom:10px;text-decoration:none;color:inherit}
.item:active{background:#F5F2EC}
.item.todo{border-left:4px solid var(--gold);padding-left:14px;background:#FFF8E9}
.item.todo .p{color:var(--seal)}
.item .p{color:#9C8F7D}
.item.todo .p{color:var(--seal)}
.item .l{flex:1;min-width:0}
.item .k{font-size:17.5px;font-weight:600;margin-bottom:6px}
.item .k span{font-weight:400;font-size:14.5px;color:var(--dim);margin-left:8px}
.item .m{font-size:15.5px;color:#5E564C;line-height:1.6;
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.item .r{text-align:right;flex:0 0 auto}
.item .p{font-size:18.5px;color:var(--seal);font-weight:700}
.item .t{font-size:13px;color:var(--dim);margin-top:5px}
.lg{display:flex;justify-content:space-between;gap:10px;text-align:center;margin:6px 0 4px}
.lg div{flex:1}
.lg b{display:block;font-size:23px;color:var(--gold);font-weight:700;line-height:1.3}
.lg span{display:block;font-size:12px;color:var(--dim);margin-top:2px;letter-spacing:.06em}
.lgs{font-size:13px;color:var(--dim);text-align:center;margin-top:10px;
 padding-top:10px;border-top:1px dashed var(--line)}
.empty{text-align:center;color:var(--dim);font-size:14px;padding:48px 0;line-height:2}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px;margin:12px 0}
.card .h{font-size:12.5px;letter-spacing:.16em;color:var(--dim);margin-bottom:12px}
.quote{font-size:16px;line-height:1.95;color:var(--ink2);white-space:pre-wrap;word-break:break-word}
audio{width:100%;margin-top:12px}
textarea{width:100%;min-height:260px;background:#fff;border:1px solid var(--line);
 border-radius:12px;padding:15px;font-family:inherit;font-size:16.5px;line-height:2.0;
 color:var(--ink);outline:none;resize:vertical}
textarea:focus{border-color:var(--gold)}
.acts{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.btn{border:1px solid var(--line);background:#fff;border-radius:10px;padding:10px 15px;
 font-size:14px;color:var(--ink2);cursor:pointer;font-family:inherit}
.btn:active{background:#F5F2EC}
.btn.gold{border-color:var(--gold);color:var(--gold)}
.btn.solid{background:var(--gold);color:#fff;border-color:var(--gold);font-weight:600}
.btn.seal{background:var(--seal);color:#fff;border-color:var(--seal);font-weight:600}
.seg{display:flex;gap:10px;align-items:flex-start;padding:14px 0;border-bottom:1px dashed var(--line)}
.seg .no{flex:0 0 26px;font-size:13px;color:var(--dim);padding-top:5px}
.seg .tx{flex:1;font-size:18px;line-height:1.85;letter-spacing:.02em}
.seg .bt{flex:0 0 auto}
.seg .bt button{border:1px solid var(--line);background:#fff;border-radius:10px;padding:14px 18px;
 font-size:15.5px;font-weight:600;color:var(--ink2);font-family:inherit;cursor:pointer;white-space:nowrap}
.seg .bt button.hot{border-color:var(--seal);color:#fff;background:var(--seal)}
.seg.done .bt button{border-color:var(--gold);color:#7B5F33;background:#F7EFDD;font-weight:600}
.back{display:inline-block;margin:18px 0 0;font-size:14px;color:var(--dim);text-decoration:none}
.done-wrap{text-align:center;padding:40px 0}
.done-wrap .ic{width:56px;height:56px;border-radius:50%;background:var(--gold);color:#fff;
 display:flex;align-items:center;justify-content:center;margin:0 auto 20px;font-size:24px}
.link{font-size:14px;word-break:break-all;background:#F5F2EC;border-radius:10px;
 padding:14px;margin:16px 0;color:var(--seal);line-height:1.7}
.tip{font-size:12.5px;color:var(--dim);line-height:1.9;margin-top:10px}

/* ---------- 提词器 ---------- */
.pm{position:fixed;inset:0;background:var(--paper);z-index:300;display:none;
 flex-direction:column;padding:12px 0 max(24px,env(safe-area-inset-bottom))}
.pm.on{display:flex}
.pm-top{display:flex;justify-content:space-between;align-items:center;
 padding:0 18px 10px;border-bottom:1px solid var(--line)}
.pm-top .x{border:0;background:transparent;font-size:26px;color:var(--dim);padding:4px 8px;line-height:1}
.pm-fs button{border:1px solid var(--line);background:#fff;border-radius:8px;
 padding:7px 11px;font-size:13.5px;margin-left:6px;color:var(--ink2);font-family:inherit}
.pm-body{flex:1;overflow:hidden;position:relative;padding:0 24px;
 -webkit-mask-image:linear-gradient(to bottom,transparent 0,#000 14%,#000 76%,transparent 99%);
 mask-image:linear-gradient(to bottom,transparent 0,#000 14%,#000 76%,transparent 99%)}
#pm-flow{will-change:transform;padding:34% 0 66%}
.pmseg{font-family:"Songti SC","Noto Serif CJK SC",serif;line-height:1.58;
 font-size:40px;color:#CFC6B6;letter-spacing:.02em;margin:0 0 36px;
 transition:color .5s ease;text-align:center}
.pmseg.cur{color:var(--ink)}
.pmseg.done{color:#B9AF9E}
.pm-hint{text-align:center;font-size:13px;color:var(--dim);padding:5px 20px 3px;letter-spacing:.05em}
.pm-speed{display:flex;align-items:center;gap:8px;padding:8px 18px 2px;justify-content:center}
.sl{font-size:13.5px;color:var(--ink2);letter-spacing:.06em;margin-right:4px}
.sp{border:1px solid var(--line);background:#fff;border-radius:10px;padding:11px 20px;
 font-size:15.5px;color:var(--ink2);font-family:inherit}
.sp.on{background:var(--gold);border-color:var(--gold);color:#fff;font-weight:600}
.pm.dark .sp{background:#121715;border-color:rgba(226,196,150,.18);color:#c9c4bc}
.pm.dark .sp.on{background:var(--gold);color:#1a1206}
.pm-bot{display:flex;gap:10px;padding:6px 18px 0}
.pm-nav{flex:1;border:1px solid var(--line);background:#fff;border-radius:12px;
 padding:15px 6px;font-size:15px;color:var(--ink2);font-family:inherit}
.pm-rec{flex:1.9;border:0;border-radius:12px;padding:16px;font-size:17px;font-weight:700;
 background:var(--seal);color:#fff;letter-spacing:.08em;font-family:inherit}
.pm-rec.off{background:#7F6A4E}
.pm-time{text-align:center;font-size:13.5px;color:var(--dim);margin-top:8px;
 font-variant-numeric:tabular-nums;min-height:19px}
.pm.dark{background:#0a0d0c}
.pm.dark .pm-top{border-color:rgba(226,196,150,.18)}
.pm.dark .pmseg{color:#57534c}
.pm.dark .pmseg.cur{color:#eae6df}
.pm.dark .pmseg.done{color:#837d75}
.pm.dark .pm-nav{background:#121715;border-color:rgba(226,196,150,.18);color:#c9c4bc}
.pm.dark .pm-fs button,.pm.dark .pm-top .x{background:#121715;border-color:rgba(226,196,150,.18);color:#c9c4bc}
.pm.dark .pm-hint,.pm.dark .pm-time{color:#7d786f}
.toast{position:fixed;left:50%;bottom:34px;transform:translateX(-50%);
 background:rgba(35,32,28,.92);color:#fff;font-size:14px;padding:11px 20px;border-radius:22px;
 opacity:0;transition:.25s;pointer-events:none;z-index:99}
.toast.on{opacity:1}
"""

DESK_HEAD = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>@@TITLE@@</title><style>@@CSS@@</style></head><body><div class="wrap">
<header>
  <img class="logo" src="/xin/m/avatar-s.png" alt="">
  <div class="brand">我的小站<small>工 作 台</small></div>
  <div class="stat">@@PRE@@<b>@@STAT@@</b></div>
</header>
"""

DESK_LIST = """@@HEAD@@
<div class="sec">等 你 动 手 · @@N1@@ 单</div>
@@TODO@@
<div class="sec">已 交 付 · @@N2@@ 单</div>
@@DONE@@
<div class="card" style="margin-top:30px;background:#F6F2E9;border-color:#E7DFCE">
  <div class="h">这 个 月 的 账 · 累 计 @@M_CNT@@ 单</div>
  <div class="lg">
    <div><b>@@M_TOTAL@@</b><span>收入（元）</span></div>
    <div><b>@@M_FEE@@</b><span>给平台</span></div>
    <div><b>@@M_NET@@</b><span>你留下</span></div>
  </div>
  <div class="lgs">@@M_BREAK@@ · 平台按 10% 收技术服务费</div>
</div>
<p class="tip">点一单，进去就是「写 / 念 / 发」。<br>钱在你微信里，这里只记账。</p>
</div>
<div class="toast" id="tst"></div></body></html>"""

DESK_ITEM = """<a class="item @@CLS@@" href="@@URL@@">
  <div class="l">
    <div class="k">@@KIND@@<span>@@META@@</span></div>
    <div class="m">@@SNIP@@</div>
  </div>
  <div class="r"><div class="p">@@PRICE@@</div><div class="t">@@AGE@@</div></div>
</a>"""

DESK_EMPTY = '<div class="empty">这里空着<br>有人写信来，就会出现在这里</div>'

DESK_DETAIL = """@@HEAD@@
<a class="back" href="@@BACK@@">← 回去</a>

<div class="card">
  <div class="h">他 说 的</div>
  <div class="quote">@@NOTE@@</div>
  @@AUDIO@@
  <div style="margin-top:12px;font-size:12.5px;color:#8C8478">
    @@META2@@
  </div>
</div>

<div class="card">
  <div class="h">一 · 写</div>
  <textarea id="draft" placeholder="点下面「让工具起一稿」，或者你自己写。">@@DRAFT@@</textarea>
  <div class="acts">
    <button class="btn gold" onclick="gen()" id="bgen">帮我写一版</button>
    <button class="btn" onclick="pol('短一点，削到四百字左右')">短一点</button>
    <button class="btn" onclick="pol('再暖一点，多加一句体贴的话')">暖一点</button>
    <button class="btn" onclick="pol('换个说法重写这一段意思，别照搬原句')">换个说法</button>
  </div>
  <div class="tip">稿子只是个底子。哪句不像你，直接改。</div>
  <button class="btn solid" style="width:100%;padding:15px;font-size:16.5px;margin-top:14px"
   onclick="nextStep()">改好了，去录音 ↓</button>
</div>

<div class="card" id="card-read">
  <div class="h" id="segh">@@SEGHEAD@@</div>
  <div id="segs">@@SEGS@@</div>
  <button class="btn solid" style="width:100%;padding:16px;font-size:16.5px;margin-top:14px"
   onclick="pmOpen()">开始念 · 打开提词器</button>
  <div class="tip">点开之后屏幕上只显示一段，字很大。<br>念错不用管，念完再重来一次就行。</div>
</div>

<div class="card" id="card-send">
  <div class="h">三 · 发</div>
  <button class="btn seal" style="width:100%;padding:15px;font-size:16px" onclick="send()" id="bsend" @@SEND_DIS@@>发 给 他</button>
  <div class="tip">点了之后生成一条链接，复制到微信发给他。</div>
</div>

</div>
<div class="pm" id="pm">
  <div class="pm-top">
    <button class="x" onclick="pmClose()">✕</button>
    <span class="pm-fs">
      <button onclick="pmDark()" id="pm-dk">夜</button>
      <button onclick="fsz(-1)">A-</button>
      <button onclick="fsz(1)">A+</button>
    </span>
  </div>
  <div class="pm-body" id="pm-body"><div id="pm-flow"></div></div>
  <div class="pm-speed">
    <span class="sl">滚动速度</span>
    <button class="sp" data-s="2.6" onclick="pset(this)">慢</button>
    <button class="sp on" data-s="3.6" onclick="pset(this)">中</button>
    <button class="sp" data-s="5.0" onclick="pset(this)">快</button>
  </div>
  <div class="pm-bot">
    <button class="pm-nav" onclick="pmReset()">回 到 开 头</button>
    <button class="pm-rec" id="pm-btn" onclick="ptog()">● 开 始 念</button>
  </div>
  <div class="pm-hint" id="pm-hint">屏幕跑太快，点「慢」；念完了它还没走完，点「快」</div>
  <div class="pm-time" id="pm-time"></div>
</div>
</div>

<div class="toast" id="tst"></div>

<input type="file" id="fa" accept="audio/*" style="display:none">
<script>
var TID=@@TID@@, NSEG=@@NSEG@@, CUR=0, OUT='@@OUT@@', TOKEN='@@TOKEN@@';
if(!canRec()){ setTimeout(function(){ toast('这个地址录不了音，要用 https 那条链接'); }, 1500); }
function toast(s){var t=document.getElementById('tst');t.textContent=s;t.classList.add('on');
  setTimeout(function(){t.classList.remove('on')},1900);}
function post(u,d){return fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify(d)}).then(function(r){return r.json()})}
function gen(){
  var b=document.getElementById('bgen'); b.disabled=true; b.textContent='正在写…';
  post('@@API@@/gen',{id:TID}).then(function(j){
    b.disabled=false; b.textContent='帮我写一版';
    if(!j.ok){toast(j.msg||'没写出来');return}
    document.getElementById('draft').value=j.text; split();
  }).catch(function(){b.disabled=false;b.textContent='帮我写一版';toast('网络不好')});
}
function pol(instr){
  var d=document.getElementById('draft').value.trim();
  if(!d){toast('先有一稿');return}
  toast('正在改…');
  post('@@API@@/polish',{id:TID,text:d,instr:instr}).then(function(j){
    if(!j.ok){toast(j.msg||'没改成');return}
    document.getElementById('draft').value=j.text; split(); toast('改好了');
  }).catch(function(){toast('网络不好')});
}
function split(){
  var t=document.getElementById('draft').value.trim();
  post('@@API@@/split',{id:TID,text:t}).then(function(j){
    if(j.ok){ document.getElementById('segs').innerHTML=j.html;
      NSEG=j.n; document.querySelector('.h').textContent=document.querySelector('.h').textContent; }
  })
}
function nextStep(){
  var t=document.getElementById('draft').value.trim();
  if(!t){toast('先写稿，或者点「帮我写一版」');return}
  post('@@API@@/split',{id:TID,text:t}).then(function(j){
    if(!j.ok){toast('没分成段');return}
    document.getElementById('segs').innerHTML=j.html;
    NSEG=j.n;
    var h=document.getElementById('segh'); if(h) h.textContent='二 · 读 · 共 '+j.n+' 段';
    document.getElementById('card-read').scrollIntoView({behavior:'smooth',block:'start'});
    toast('分成 '+j.n+' 段了，往下念');
  }).catch(function(){toast('网络不好')});
}

var REC=null, CH=[], RT0=0, RTM=null;
function canRec(){ return !!(window.isSecureContext && navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder); }
function segBtn(i){ var d=document.getElementById('seg'+i); return d? d.querySelector('button'):null; }

function recErr(e){
  var n=(e&&e.name)?e.name:'';
  if(/MicroMessenger/i.test(navigator.userAgent)) return '微信里录不了音，用 App 或者浏览器打开';
  if(n==='NotAllowedError'||n==='SecurityError') return '麦克风被拒绝了：点地址栏左边，允许麦克风';
  if(n==='NotFoundError'||n==='DevicesNotFoundError') return '没找到麦克风';
  if(n==='NotReadableError') return '麦克风被别的应用占着，先关掉别的';
  return '麦克风没打开，再点一次';
}


/* ---------- 提词器 ---------- */
var PMI=0,
    PMSZ=parseInt(localStorage.getItem('pm_sz')||'36')||36,
    PMRATE=parseFloat(localStorage.getItem('pm_rate')||'3.6')||3.6,
    PMST=null, PMT0=0, PMTM=null,
    PMS={raf:null,y:0,dist:0,speed:0,last:0,paused:true,started:false,run:false},
    PMAC=null, PMAN=null, PMVAD=null, PMQUIET=0;

function pmList(){
  var a=[];
  document.querySelectorAll('#segs .seg .tx').forEach(function(el){ a.push(el.textContent.trim()); });
  return a;
}
function pmOpen(){
  var a=pmList();
  if(!a.length){ toast('先把稿子写好'); return; }
  var el=document.getElementById('pm');
  el.classList.add('on');
  if(!window._pmTap){
    window._pmTap=1;
    document.getElementById('pm-body').addEventListener('click',function(){
      if(REC && REC.state==='recording'){
        PMS.paused=!PMS.paused;
        document.getElementById('pm-hint').textContent = PMS.paused
          ? '停住了。再点一下屏幕，继续走' : '走着呢。点屏幕可以停';
      }
    });
  }
  if(localStorage.getItem('pm_dark')==='1') el.classList.add('dark');
  pmBuild();
}
function pmClose(){
  if(REC && REC.state==='recording'){ pmStop(true); }
  PMS.run=false; if(PMS.raf) cancelAnimationFrame(PMS.raf);
  document.getElementById('pm').classList.remove('on');
  clearInterval(PMTM);
}
function pmBuild(){
  var a=pmList(), h='';
  a.forEach(function(t,i){ h+='<div class="pmseg" data-i="'+i+'" style="font-size:'+PMSZ+'px">'+t+'</div>'; });
  document.getElementById('pm-flow').innerHTML=h;
  PMS.y=0; PMS.started=true; PMS.paused=true; PMS.last=0;
  document.getElementById('pm-time').textContent='';
  document.querySelectorAll('.pm-speed .sp').forEach(function(b){
    b.classList.toggle('on', Math.abs(parseFloat(b.dataset.s)-PMRATE)<0.3);
  });
  pmApply(); pmMark(); pmCalc();
}
function pmApply(){
  var f=document.getElementById('pm-flow');
  if(f) f.style.transform='translateY('+(-PMS.y)+'px)';
}
function pmMark(){
  var segs=document.querySelectorAll('.pmseg');
  if(!segs.length) return;
  var box=document.getElementById('pm-body').clientHeight;
  var mid=PMS.y+box*0.34, idx=0;
  for(var i=0;i<segs.length;i++){ if(segs[i].offsetTop<=mid) idx=i; }
  for(var k=0;k<segs.length;k++){
    segs[k].className='pmseg'+(k===idx?' cur':'')+(k<idx?' done':'');
  }
  PMI=idx;
}
function pmCalc(){
  var flow=document.getElementById('pm-flow');
  var view=document.getElementById('pm-body').clientHeight;
  var chars=pmList().join('').length;
  PMS.dist=Math.max(0, flow.scrollHeight-view);
  var secs=chars/PMRATE;
  PMS.speed = secs>0 ? PMS.dist/secs : 0;
}
function pmLoop(ts){
  if(!PMS.run) return;
  if(!PMS.last) PMS.last=ts;
  var dt=(ts-PMS.last)/1000; PMS.last=ts;
  if(dt>0 && dt<0.5 && !PMS.paused){
    PMS.y += PMS.speed*dt;
    if(PMS.y>PMS.dist){ PMS.y=PMS.dist; }
    pmApply(); pmMark();
  }
  PMS.raf=requestAnimationFrame(pmLoop);
}
function pset(el){
  PMRATE=parseFloat(el.dataset.s)||3.6;
  localStorage.setItem('pm_rate',PMRATE);
  document.querySelectorAll('.pm-speed .sp').forEach(function(b){ b.classList.remove('on'); });
  el.classList.add('on');
  pmCalc();
  PMS.last=0;
}
function fsz(d){
  PMSZ=Math.max(24,Math.min(80,PMSZ+d*4));
  localStorage.setItem('pm_sz',PMSZ);
  document.querySelectorAll('.pmseg').forEach(function(el){ el.style.fontSize=PMSZ+'px'; });
  pmCalc(); pmMark();
}
function pspd(d){
  PMRATE=Math.max(2.5,Math.min(7,PMRATE+d*0.4));
  localStorage.setItem('pm_rate',PMRATE);
  pmCalc();
  var h=document.getElementById('pm-hint');
  h.textContent='按每秒 '+PMRATE.toFixed(1)+' 个字算的，念快了就调快一点';
  clearTimeout(window._pmh);
  window._pmh=setTimeout(function(){ h.textContent='开始念之后，说到哪儿它跟到哪儿。停下来，它也停。'; },2000);
}
function pmReset(){
  PMS.y=0; PMS.started=true; PMS.paused=true; PMS.last=0;
  pmApply(); pmMark();
}
function pmDark(){
  var el=document.getElementById('pm');
  el.classList.toggle('dark');
  localStorage.setItem('pm_dark', el.classList.contains('dark')?'1':'0');
}
function ptog(){
  if(REC && REC.state==='recording'){ pmStop(false); return; }
  pmStart();
}
function pmStart(){
  var b=document.getElementById('pm-btn');
  navigator.mediaDevices.getUserMedia({audio:true}).then(function(st){
    PMST=st; CH=[]; PMT0=Date.now();
    var mime='';
    ['audio/webm;codecs=opus','audio/webm','audio/mp4','audio/ogg'].forEach(function(m){
      if(!mime && window.MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(m)) mime=m;
    });
    REC = mime ? new MediaRecorder(st,{mimeType:mime}) : new MediaRecorder(st);
    REC.ondataavailable=function(e){ if(e.data && e.data.size) CH.push(e.data); };
    REC.start();
    b.textContent='❚❚ 停 一 下';
    b.classList.add('off');
    pmCalc();
    PMS.run=true; PMS.last=0; PMS.paused=false; PMS.started=true;
    PMS.raf=requestAnimationFrame(pmLoop);
    PMTM=setInterval(function(){
      var sec=Math.floor((Date.now()-PMT0)/1000);
      document.getElementById('pm-time').textContent='录音中  '+Math.floor(sec/60)+':'+('0'+(sec%60)).slice(-2);
    },300);
  }).catch(function(e){ toast(recErr(e)); });
}
function pmStop(cancel){
  clearInterval(PMTM);
  var b=document.getElementById('pm-btn');
  b.textContent='● 开始念'; b.classList.remove('off');
  PMS.run=false; if(PMS.raf) cancelAnimationFrame(PMS.raf);
  if(!REC || REC.state!=='recording'){ document.getElementById('pm-time').textContent=''; return; }
  if(cancel){
    REC.onstop=function(){ if(PMST) PMST.getTracks().forEach(function(t){t.stop()}); };
    REC.stop(); document.getElementById('pm-time').textContent=''; return;
  }
  REC.onstop=function(){
    if(PMST) PMST.getTracks().forEach(function(t){t.stop()});
    uploadTake();
  };
  REC.stop();
}
function uploadTake(){
  document.getElementById('pm-time').textContent='正在保存…';
  var blob=new Blob(CH,{type:CH[0]?CH[0].type:'audio/webm'});
  if(blob.size<3000){ toast('这段太短了，再念一次'); document.getElementById('pm-time').textContent=''; return; }
  var fd=new FormData();
  fd.append('f', blob, 'take.'+(blob.type.indexOf('mp4')>=0?'m4a':'webm'));
  fd.append('id', TID);
  fetch('@@API@@/take',{method:'POST',body:fd}).then(function(r){return r.json()}).then(function(j){
    if(!j.ok){ toast(j.msg||'没存上'); document.getElementById('pm-time').textContent=''; return; }
    OUT=j.url;
    document.getElementById('pm-time').textContent='好了，可以发了';
    var sb=document.getElementById('bsend'); if(sb) sb.style.opacity=1;
    setTimeout(function(){ document.getElementById('pm').classList.remove('on'); }, 1000);
    toast('录音好了，往下发给客户');
    setTimeout(function(){ document.getElementById('card-send').scrollIntoView({behavior:'smooth'}); }, 1100);
  }).catch(function(){ toast('网络不好，再按一次'); document.getElementById('pm-time').textContent=''; });
}
function rec(i){
  CUR=i;
  if(!canRec()){ document.getElementById('fa').click(); return; }
  if(REC && REC.state==='recording'){ stopRec(); return; }
  startRec();
}
function startRec(){
  var btn=segBtn(CUR);
  navigator.mediaDevices.getUserMedia({audio:true}).then(function(st){
    CH=[]; RT0=Date.now();
    var mime='';
    ['audio/webm;codecs=opus','audio/webm','audio/mp4','audio/ogg'].forEach(function(m){
      if(!mime && window.MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(m)) mime=m;
    });
    REC = mime ? new MediaRecorder(st,{mimeType:mime}) : new MediaRecorder(st);
    REC.ondataavailable=function(e){ if(e.data && e.data.size) CH.push(e.data); };
    REC.onstop=function(){ st.getTracks().forEach(function(t){t.stop()}); uploadSeg(); };
    REC.start();
    if(btn) btn.textContent='录音中 · 点此结束';
    RTM=setInterval(function(){
      var sec=Math.floor((Date.now()-RT0)/1000);
      if(btn) btn.textContent='● '+Math.floor(sec/60)+':'+('0'+(sec%60)).slice(-2)+' 点此结束';
    },300);
  }).catch(function(e){
    var m=recErr(e);
    if(btn) btn.textContent='点此重试';
    toast(m);
    setTimeout(function(){ if(btn) btn.textContent='录这段'; },3000);
  });
}
function stopRec(){
  clearInterval(RTM);
  var btn=segBtn(CUR); if(btn) btn.textContent='上传中…';
  if(REC && REC.state==='recording') REC.stop();
}
function uploadSeg(){
  var btn=segBtn(CUR);
  var blob=new Blob(CH,{type:CH[0]?CH[0].type:'audio/webm'});
  if(blob.size<1200){ if(btn) btn.textContent='太短'; toast('这段太短了，重录'); return; }
  var fd=new FormData();
  fd.append('f', blob, 'seg.'+(blob.type.indexOf('mp4')>=0?'m4a':'webm'));
  fd.append('id', TID); fd.append('seg', CUR+1); fd.append('seq','0');
  fetch('@@API@@/seg',{method:'POST',body:fd}).then(function(r){return r.json()}).then(function(j){
    if(!j.ok){ if(btn) btn.textContent='重录'; toast('没传上去'); return; }
    var d=document.getElementById('seg'+CUR); if(d) d.classList.add('done');
    if(btn) btn.textContent='已录 ✓';
    toast('第 '+(CUR+1)+' 段好了');
  }).catch(function(){ if(btn) btn.textContent='重录'; toast('网络不好'); });
}
document.getElementById('fa').addEventListener('change', function(e){
  var f=e.target.files[0]; if(!f) return;
  var bt=document.querySelector('#seg'+CUR+' button');
  if(bt){bt.textContent='上传中…';}
  var fd=new FormData(); fd.append('f',f); fd.append('id',TID);
  fd.append('seg',CUR+1); fd.append('seq',(document.getElementById('seq')||{}).value||'0');
  fetch('@@API@@/seg',{method:'POST',body:fd}).then(function(r){return r.json()}).then(function(j){
    if(!j.ok){if(bt)bt.textContent='重录'; toast('没传上去');return}
    var d=document.getElementById('seg'+CUR); if(d)d.classList.add('done');
    if(bt)bt.textContent='已录 ✓';
    toast('第 '+(CUR+1)+' 段好了');
  }).catch(function(){if(bt)bt.textContent='重录';toast('网络不好')});
});
function merge(){
  var b=document.getElementById('bmerge'); b.disabled=true; b.textContent='正在合成…';
  post('@@API@@/merge',{id:TID}).then(function(j){
    b.disabled=false; b.textContent='都录好了，合成';
    if(!j.ok){toast(j.msg||'还没录全');return}
    OUT=j.url; toast('合成了，可以发');
    document.getElementById('card-send').style.display='block';
    document.getElementById('card-send').scrollIntoView({behavior:'smooth'});
  }).catch(function(){b.disabled=false;b.textContent='都录好了，合成';toast('网络不好')});
}
function send(){
  if(!OUT){toast('先把录音合成，再发');return}
  var b=document.getElementById('bsend'); b.disabled=true;
  post('@@API@@/send',{id:TID}).then(function(j){
    b.disabled=false;
    if(!j.ok){toast(j.msg||'没发出去');return}
    location.href=j.page;
  }).catch(function(){b.disabled=false;toast('网络不好')});
}
</script></body></html>"""

SEG_TPL = """<div class="seg" id="seg@@I@@">
  <div class="no">@@N@@</div>
  <div class="tx serif">@@TX@@</div>
</div>"""


def desk_head(stat, title="工作台", pre="本月", css=DESK_CSS):
    return (DESK_HEAD.replace("@@CSS@@", css).replace("@@TITLE@@", title)
            .replace("@@PRE@@", pre).replace("@@STAT@@", stat))


def seg_html(i, text):
    return (SEG_TPL.replace("@@I@@", str(i)).replace("@@N@@", str(i + 1)).replace("@@TX@@", text))


# ============================================================ 交付页（信纸）
DE_CSS = """
:root{--paper:#FBF8F2;--ink:#2B2620;--ink2:#4A423A;--dim:#8C8274;--line:#E6DCCB;--gold:#8A6E4B;--seal:#A2503F}
body{background:var(--paper);color:var(--ink);margin:0;
 font-family:"Songti SC","Noto Serif CJK SC","STSong",serif;font-size:18px;line-height:2.05;
 letter-spacing:.3px;padding:54px 26px 70px}
.wrap{max-width:600px;margin:0 auto}
.mark{width:64px;height:64px;border-radius:50%;display:block;margin:0 auto 30px;
 object-fit:cover;box-shadow:0 0 0 1px rgba(162,80,63,.28)}
.head{text-align:center;font-size:14px;letter-spacing:.16em;color:var(--dim);margin-bottom:40px}
.body{white-space:pre-wrap;font-size:18.5px;line-height:2.15;color:var(--ink)}
.body p{margin:0 0 1.1em}
h2{font-size:16px;font-weight:400;color:var(--gold);letter-spacing:.2em;margin:0 0 22px}
.player{margin:38px 0 30px;padding:26px 22px;background:#fff;
 border:1px solid var(--line);border-radius:14px;text-align:center}
.player .lab{font-size:12.5px;letter-spacing:.22em;color:var(--dim);margin-bottom:16px}
.player .play{width:66px;height:66px;border-radius:50%;background:var(--gold);border:0;
 color:#fff;font-size:24px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center}
.player .bar{height:3px;background:var(--line);border-radius:2px;margin:20px 4px 8px;position:relative;overflow:hidden}
.player .bar i{position:absolute;left:0;top:0;height:100%;width:0;background:var(--gold);display:block}
.player .tm{font-size:12px;color:var(--dim);font-variant-numeric:tabular-nums}
.sign{margin-top:46px;text-align:right;font-size:17px;color:var(--ink2);letter-spacing:.1em}
.sign small{display:block;font-size:12.5px;color:var(--dim);letter-spacing:.14em;margin-top:6px}
.foot{margin-top:56px;padding-top:22px;border-top:1px solid var(--line);
 font-size:11.5px;color:var(--dim);line-height:2;text-align:center;letter-spacing:.06em}
"""

DE_HTML = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>@@TITLE@@</title><style>@@CSS@@</style></head><body><div class="wrap">
<img class="mark" src="/xin/m/avatar.png" alt="">
<div class="head">@@BRAND@@</div>
@@PLAYER@@
<div class="body">@@BODY@@</div>
@@TEXT_AFTER@@
<div class="sign">@@SIGN@@<small>@@SIGNSUB@@</small></div>
<div class="foot">本服务为个人书信回复，不构成心理咨询、诊断或治疗<br>
如你或身边的人正处于困境，请拨打心理援助热线 12356</div>
</div>
@@SCRIPT@@
</body></html>"""

PLAYER_HTML = """<div class="player">
  <div class="lab">他 念 给 你 听</div>
  <button class="play" id="pb" onclick="tg()">▶</button>
  <div class="bar"><i id="pi"></i></div>
  <div class="tm"><span id="tn">0:00</span> / <span id="td">0:00</span></div>
  <audio id="au" src="@@URL@@"></audio>
</div>"""

PLAYER_JS = """
<script>
var au=document.getElementById('au'), pb=document.getElementById('pb'),
    pi=document.getElementById('pi'), tn=document.getElementById('tn'), td=document.getElementById('td');
function fmt(s){s=Math.floor(s||0);return Math.floor(s/60)+':'+('0'+(s%60)).slice(-2)}
au.addEventListener('loadedmetadata',function(){td.textContent=fmt(au.duration)});
au.addEventListener('timeupdate',function(){
  pi.style.width=(au.currentTime/(au.duration||1)*100)+'%'; tn.textContent=fmt(au.currentTime)});
au.addEventListener('ended',function(){pb.textContent='▶';pi.style.width='0'});
function tg(){ if(au.paused){au.play();pb.textContent='❚❚'} else {au.pause();pb.textContent='▶'} }
</script>"""


def deliver_page(cfg):
    h = DE_HTML
    for k, v in cfg.items():
        h = h.replace("@@" + k + "@@", str(v))
    return h


OPS_HTML = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>运营 · 小站的信</title><style>@@CSS@@</style></head><body><div class="wrap">
<header>
  <img class="logo" src="/xin/m/avatar-s.png" alt="">
  <div class="brand">运营看板<small>野 山 下 的 小 站</small></div>
  <div class="stat">本月<b>@@TOTAL@@ 元</b></div>
</header>

<div class="sec">本 月 概 况</div>
<div class="card">
  <div class="lg">
    <div><b>@@CNT@@</b><span>单</span></div>
    <div><b>@@TOTAL@@</b><span>元</span></div>
    <div><b>@@FEE@@</b><span>应结（元）</span></div>
  </div>
  <div class="lgs">@@BREAK@@</div>
</div>

<div class="sec">待 处 理 · @@TODO_N@@ 单</div>
@@TODO@@

<div class="sec">近 14 天</div>
<div class="card">@@BARS@@</div>

<div class="sec">收 款 码</div>
<div class="card" style="text-align:center">
  <img id="payimg" src="/xin/m/pay.png?v=0" alt="" style="width:190px;height:190px;
   object-fit:contain;background:#fff;border-radius:10px;padding:6px"
   onerror="this.style.display='none';document.getElementById('payna').style.display='block'">
  <div id="payna" style="display:none;font-size:14px;color:#8C8478;padding:26px 0">
    还没设置收款码</div>
  <p style="font-size:13px;color:#8C8478;margin:12px 0 14px;line-height:1.8">
    这个码会显示在客户提交之后。<br>传一张微信收款码截屏就行，会自动裁成方形。</p>
  <input type="file" id="payf" accept="image/*" style="display:none" onchange="upPay(this)">
  <button class="btn gold" style="width:100%;padding:14px;font-size:15px"
   onclick="document.getElementById('payf').click()">上 传 / 更 换 收 款 码</button>
</div>

<div class="sec">最 近 交 付</div>
@@RECENT@@

<p class="tip">这一页只有你能打开。<br>链接别外传，换了密钥这里就失效。</p>
</div>
<script>
function upPay(el){
  var f=el.files[0]; if(!f) return;
  var fd=new FormData(); fd.append('f',f); fd.append('key','@@OPSKEY@@');
  var bt=el.parentNode.querySelector('button');
  bt.textContent='上传中…';
  fetch('/xin/api/pay',{method:'POST',body:fd}).then(function(r){return r.json()}).then(function(j){
    if(!j.ok){ bt.textContent='失败：'+(j.msg||''); return; }
    var im=document.getElementById('payimg');
    im.src='/xin/m/pay.png?v='+j.v; im.style.display='block';
    document.getElementById('payna').style.display='none';
    bt.textContent='换 好 了 ✓';
    setTimeout(function(){ bt.textContent='上 传 / 更 换 收 款 码'; },2000);
  }).catch(function(){ bt.textContent='网络不好，再试一次'; });
}
</script></body></html>"""


def ops_page(cfg):
    h = OPS_HTML
    for k, v in cfg.items():
        h = h.replace("@@" + k + "@@", str(v))
    return h
