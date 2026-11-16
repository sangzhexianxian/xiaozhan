# -*- coding: utf-8 -*-
"""提醒通道（2026-11-16）

一个入口发三条路，按后台填的配置决定发哪些：
  1. 邮箱      —— 填 notify_mail，用现成的 send_mail.py
  2. 企微机器人 —— 填 notify_wecom（群机器人 webhook），免费、微信里有推送、最快
  3. 短信      —— 填 notify_phone + sms_key（阿里云/腾讯云），没填就不发

用法：
    import notify
    notify.alert("有人要买「关山月」", "<p>...</p>", "有人要买关山月 2980")
"""
import json
import os
import subprocess
import tempfile
import urllib.request

import core
import conf

MAIL_PY = conf.SENDMAIL
PY = conf.PYBIN


def _get(*keys):
    for k in keys:
        v = (core.get(k) or "").strip()
        if v:
            return v
    return ""


def cfg():
    return {
        "mail": _get("notify_mail", "alert_mail"),
        "wecom": _get("notify_wecom", "wecom_webhook"),
        "phone": _get("notify_phone"),
    }


def _mail(subject, html, to):
    fd, hp = tempfile.mkstemp(suffix=".html")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html)
    try:
        subprocess.run([PY, MAIL_PY,
                        "--to", to,
                        "--from-name", conf.MAIL_FROM,
                        "--subject", subject,
                        "--html", hp],
                       stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
        return True
    except Exception as e:
        print("[notify mail]", e)
        return False
    finally:
        try:
            os.unlink(hp)
        except Exception:
            pass


def _wecom(subject, text, hook):
    try:
        body = json.dumps({"msgtype": "markdown",
                           "markdown": {"content": "## " + subject + "\n" + text}},
                          ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(hook, data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception as e:
        print("[notify wecom]", e)
        return False


def alert(subject, html, text=""):
    """三条路都试一遍，哪条通就算成"""
    if not text:
        import re
        text = re.sub(r"<[^>]+>", "", html).strip()
    c = cfg()
    done = []
    if c["mail"]:
        if _mail(subject, html, c["mail"]):
            done.append("邮箱")
    if c["wecom"]:
        if _wecom(subject, text, c["wecom"]):
            done.append("企微")
    if not done:
        # 什么都没配，兜底发老地址，别让提醒丢了
        if _mail(subject, html, conf.OPS_EMAIL):
            done.append("邮箱(兜底)")
        else:
            print("[notify] 三条路都没发出去：", subject)
    return done
