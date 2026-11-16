# -*- coding: utf-8 -*-
"""真人预约 · 到点提醒（每 10 分钟）
cron: 每 10 分钟跑一次（按需）
"""
import os
import sqlite3
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
import live  # noqa
import conf

TO = conf.OPS_EMAIL
MAIL = conf.SENDMAIL
PY = conf.PYBIN
STATE = "/tmp/live_alerted.json"


def _seen():
    try:
        import json
        return set(json.load(open(STATE, encoding="utf-8")))
    except Exception:
        return set()


def _save(s):
    import json
    try:
        json.dump(list(s)[-300:], open(STATE, "w", encoding="utf-8"))
    except Exception:
        pass


def main():
    now = time.time()
    seen = _seen()
    c = sqlite3.connect(core.DB)
    c.row_factory = sqlite3.Row
    rows = c.execute("""SELECT b.*, u.phone, u.nick FROM booking b
                        LEFT JOIN usr u ON u.id=b.uid WHERE b.status='booked'""").fetchall()
    c.close()
    hit = []
    for r in rows:
        try:
            t = time.mktime(live._dt(r["slot"]))
        except Exception:
            continue
        dm = (t - now) / 60.0
        if 0 <= dm <= 60 and str(r["id"]) not in seen:
            hit.append(r)
            seen.add(str(r["id"]))
    if not hit:
        return
    _save(seen)

    body = ['<div style="font-family:-apple-system,sans-serif;padding:8px">',
            '<h2 style="font-size:17px;margin:0 0 12px">一小时后要跟人说话</h2>',
            '<table cellpadding="7" cellspacing="0" style="font-size:14px;border-collapse:collapse">']
    for r in hit:
        body.append('<tr><td style="color:#888;padding-right:18px">%s</td>'
                    '<td><b>%s</b> · %s · ￥%s</td></tr>'
                    % (r["slot"], (r["nick"] or ""), live.LABEL.get(r["kind"], ""), r["amount"]))
    body.append("</table>")
    body.append('<p style="font-size:13px;color:#555;margin-top:14px">'
                '到点了，用微信语音拨过去。聊完记得在后台点「做完了」。</p>')
    body.append('<p style="font-size:13px"><a href="' + conf.u("/xin/liveops/") + '%s">看预约</a></p>'
                % core.get("ops_key"))
    body.append("</div>")

    hp = "/tmp/live_alert.html"
    with open(hp, "w", encoding="utf-8") as f:
        f.write("".join(body))
    subj = "约的人要来了 · %s · %d 单" % (hit[0]["slot"][5:16], len(hit))
    r = subprocess.run([PY, MAIL, "--to", TO, "--from-name", conf.MAIL_FROM,
                        "--subject", subj, "--html", hp],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
    print(subj)
    print((r.stdout or "")[-200:])


if __name__ == "__main__":
    main()
