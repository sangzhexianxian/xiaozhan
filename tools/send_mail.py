#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""极简发信脚本（各处通过 subprocess 调用）

用法：
  python3 send_mail.py --to a@b.com --from-name 小站 --subject 标题 --html body.html
  python3 send_mail.py ... --inline cover=/path/a.jpg --attach /path/x.mp4 /path/y.pdf

配置从环境变量读，也会自动加载项目根目录的 .env：
  SMTP_HOST  SMTP_PORT(465 或 587)  SMTP_USER  SMTP_PASS
"""
import argparse
import mimetypes
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formataddr, formatdate

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_env():
    for p in (os.path.join(ROOT, ".env"), os.path.join(HERE, ".env")):
        if not os.path.exists(p):
            continue
        try:
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception:
            pass


load_env()

HOST = os.environ.get("SMTP_HOST", "smtp.qq.com")
PORT = int(os.environ.get("SMTP_PORT", "465") or 465)
USER = os.environ.get("SMTP_USER", "")
PASS = os.environ.get("SMTP_PASS", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True)
    ap.add_argument("--from-name", default="小站")
    ap.add_argument("--subject", required=True)
    ap.add_argument("--html", default="")
    ap.add_argument("--text", default="")
    ap.add_argument("--inline", nargs="*", default=[], help="name=path，正文里用 cid:name")
    ap.add_argument("--attach", nargs="*", default=[])
    a = ap.parse_args()

    if not USER or not PASS:
        print("MAIL_SKIP 没配 SMTP_USER / SMTP_PASS", file=sys.stderr)
        return 2

    html = ""
    if a.html and os.path.exists(a.html):
        html = open(a.html, encoding="utf-8").read()

    msg = EmailMessage()
    msg["Subject"] = a.subject
    msg["From"] = formataddr((a.from_name, USER))
    msg["To"] = a.to
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(a.text or "（本邮件正文为 HTML，请用支持 HTML 的客户端查看）")

    if html:
        msg.add_alternative(html, subtype="html")
        part = msg.get_payload()[-1]
        for item in a.inline:
            if "=" not in item:
                continue
            name, path = item.split("=", 1)
            if not os.path.exists(path):
                continue
            ctype = mimetypes.guess_type(path)[0] or "image/png"
            maintype, subtype = ctype.split("/", 1)
            with open(path, "rb") as f:
                part.add_related(f.read(), maintype=maintype, subtype=subtype,
                                 cid="<%s>" % name, filename=os.path.basename(path))

    for path in a.attach:
        if not os.path.exists(path):
            continue
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(path, "rb") as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype,
                               filename=os.path.basename(path))

    ctx = ssl.create_default_context()
    try:
        if PORT == 465:
            s = smtplib.SMTP_SSL(HOST, PORT, context=ctx, timeout=60)
        else:
            s = smtplib.SMTP(HOST, PORT, timeout=60)
            s.starttls(context=ctx)
        s.login(USER, PASS)
        s.send_message(msg)
        s.quit()
        print("MAIL_OK %s | %s" % (a.to, a.subject))
        return 0
    except Exception as e:
        print("MAIL_FAIL %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
