# -*- coding: utf-8 -*-
"""积压告警：有单超过 24 小时没处理，或累计超过 5 单，发邮件"""
import os
import sqlite3
import subprocess
import time
import conf

DB = os.path.join(BASE, "data", "letters.db")
MAIL = conf.SENDMAIL
PY = conf.PYBIN
TO = conf.OPS_EMAIL
STATE = os.path.join(BASE, "data", "alert_state.txt")


def hours(t):
    try:
        return (time.time() - time.mktime(time.strptime(t, "%Y-%m-%d %H:%M:%S"))) / 3600
    except Exception:
        return 0


c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
rows = c.execute("SELECT * FROM threads WHERE status='pending' ORDER BY id").fetchall()
m = time.strftime("%Y-%m")
paid = c.execute("SELECT COUNT(*) n, COALESCE(SUM(price),0) s FROM threads "
                 "WHERE status IN ('paid','done') AND created LIKE ?", (m + "%",)).fetchone()
c.close()

if not rows:
    print("no pending")
    raise SystemExit(0)

stale = [r for r in rows if hours(r["created"]) >= 24]
n, total = paid["n"], paid["s"]

if not stale and len(rows) < 5:
    print("ok, pending=%d, none stale" % len(rows))
    raise SystemExit(0)

today = time.strftime("%Y-%m-%d")
sig = "%s|%d|%d" % (today, len(rows), len(stale))
try:
    if open(STATE).read().strip() == sig:
        print("already sent today")
        raise SystemExit(0)
except Exception:
    pass

items = ""
for r in rows:
    h = hours(r["created"])
    items += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>￥%d</td>"
              "<td style='color:%s'>%.1f 小时</td></tr>"
              % (r["id"], "回信" if r["kind"] == "reply" else "代读",
                 (r["nick"] or "没留名"), r["price"],
                 "#c0392b" if h >= 24 else "#888", h))

html = """<div style="font-family:-apple-system,'PingFang SC',sans-serif;max-width:640px">
<h3 style="color:#A2503F;margin:0 0 14px">小站的信 · 积压提醒</h3>
<p>现在有 <b>%d</b> 单没处理，其中 <b style="color:#A2503F">%d 单超过 24 小时</b>。</p>
<p style="color:#666;font-size:13px">本月已交付 %d 单 · %d 元</p>
<table style="border-collapse:collapse;width:100%%;font-size:13px;margin-top:14px">
<tr style="background:#f6f2e9"><th align="left" style="padding:7px 6px">#</th>
<th align="left">类型</th><th align="left">谁</th><th align="left">金额</th>
<th align="left">已等</th></tr>
%s
</table>
<p style="margin-top:18px"><a href="@@SITE@@/d"
style="background:#8A6E4B;color:#fff;padding:10px 20px;border-radius:8px;
text-decoration:none;font-size:14px">去工作台看看</a></p>
<p style="color:#999;font-size:12px;margin-top:16px">
系统自动发的。同一情况一天只提醒一次。</p></div>""" % (
    len(rows), len(stale), n, total, items)

html = html.replace("@@SITE@@", conf.SITE)

p = "/tmp/xin_alert.html"
open(p, "w", encoding="utf-8").write(html)

subprocess.run([PY, MAIL, "--to", TO, "--from-name", conf.MAIL_FROM,
                "--subject", "【积压】%d 单待处理，%d 单超 24 小时" % (len(rows), len(stale)),
                "--html", p], check=False)

open(STATE, "w").write(sig)
print("sent: pending=%d stale=%d" % (len(rows), len(stale)))
