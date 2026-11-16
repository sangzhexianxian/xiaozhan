# -*- coding: utf-8 -*-
"""数字分身 · 每日用量日报（超线会标红）
cron: 每天晚上跑一次（按需）
"""
import os
import sqlite3
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chat  # noqa
import conf

TO = conf.OPS_EMAIL
MAIL = conf.SENDMAIL
PY = conf.PYBIN
TTS_UNIT = 8.0       # 元 / 万字符（复刻音色后付费价）
LLM_UNIT = 1.0       # 元 / 百万 token（粗估未命中价）


def main():
    d = time.strftime("%Y-%m-%d")
    c = sqlite3.connect(chat.core.DB)
    c.row_factory = sqlite3.Row
    u = c.execute("SELECT chars,n FROM tts_use WHERE d=?", (d,)).fetchone()
    uc = (u["chars"] if u else 0) or 0
    un = (u["n"] if u else 0) or 0

    turns = c.execute("SELECT COUNT(*) n FROM chat WHERE role='u' AND created LIKE ?",
                      (d + "%",)).fetchone()["n"]
    sess = c.execute("SELECT COUNT(DISTINCT sid) n FROM chat WHERE created LIKE ?",
                     (d + "%",)).fetchone()["n"]
    newbie = c.execute("SELECT COUNT(*) n FROM ent WHERE created LIKE ?",
                       (d + "%",)).fetchone()["n"]
    cards = c.execute("SELECT COUNT(*) n FROM ent WHERE paid_until >= ?", (d,)).fetchone()["n"]
    crisis = c.execute("SELECT COUNT(*) n FROM chat WHERE crisis=1 AND created LIKE ?",
                       (d + "%",)).fetchone()["n"]
    c.close()

    cost = uc / 10000.0 * TTS_UNIT
    over = uc >= chat.TTS_WARN_CHARS
    flag = "⚠️ " if over else ""

    rows = [
        ("对话轮数", "%d 轮（日限 %d）" % (turns, chat.GLOBAL_DAY_MAX)),
        ("语音合成", "%d 段 · %d 字" % (un, uc)),
        ("语音费用", "约 %.2f 元（%.0f 元/万字符）" % (cost, TTS_UNIT)),
        ("活跃会话", "%d 个（今天新增 %d）" % (sess, newbie)),
        ("付费周卡", "%d 个（在有效期内）" % cards),
        ("熔断", "%d 次" % crisis),
    ]
    body = ['<h2 style="font-size:17px;color:#1a1a1a;margin:0 0 14px">数字分身 · %s 用量</h2>' % d,
            '<table cellpadding="7" cellspacing="0" style="border-collapse:collapse;font-size:14px">']
    for k, v in rows:
        body.append('<tr><td style="color:#888;border-bottom:1px solid #eee;padding-right:22px">%s</td>'
                    '<td style="border-bottom:1px solid #eee"><b>%s</b></td></tr>' % (k, v))
    body.append('</table>')
    if over:
        body.append('<p style="color:#c0392b;font-size:13px;margin-top:14px">'
                    '字数已超过告警线 %d，检查一下是不是有人在刷。</p>' % chat.TTS_WARN_CHARS)
    else:
        body.append('<p style="color:#999;font-size:12px;margin-top:14px">'
                    '告警线 %d 字（约 %.1f 元）</p>' % (chat.TTS_WARN_CHARS,
                                                      chat.TTS_WARN_CHARS / 10000.0 * TTS_UNIT))
    body.append('<p style="font-size:12px;margin-top:16px">'
                '<a href="' + conf.u("/xin/chatlog/") + '%s">看运营页</a></p>'
                % chat.core.get("ops_key"))

    hp = "/tmp/xin_daily.html"
    with open(hp, "w", encoding="utf-8") as f:
        f.write("<div style=\"font-family:-apple-system,'PingFang SC',sans-serif;padding:6px\">"
                + "".join(body) + "</div>")
    subj = "%s数字分身 · %s · %d轮 %.1f元" % (flag, d[5:], turns, cost)
    r = subprocess.run([PY, MAIL, "--to", TO, "--from-name", conf.MAIL_FROM,
                        "--subject", subj, "--html", hp],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
    print(subj)
    print((r.stdout or "")[-300:], (r.stderr or "")[-300:])


if __name__ == "__main__":
    main()
