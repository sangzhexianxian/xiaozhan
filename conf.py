# -*- coding: utf-8 -*-
"""站点配置层

所有会变的东西都在这里，代码里不再出现具体域名、邮箱、密钥。
优先读环境变量，也支持同目录下的 .env 文件（见 .env.example）。
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))


def _load_env():
    p = os.path.join(BASE, ".env")
    if not os.path.exists(p):
        return
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception:
        pass


_load_env()


def _g(k, d=""):
    return os.environ.get(k) or d


# ---------------------------------------------------------------- 站点
SITE = _g("SITE_BASE").rstrip("/") or "http://127.0.0.1:8000"
OPS_EMAIL = _g("OPS_EMAIL")
MAIL_FROM = _g("MAIL_FROM_NAME", "我的小站")

# ---------------------------------------------------------------- 环境
PYBIN = _g("PYTHON_BIN") or sys.executable or "python3"
FFMPEG = _g("FFMPEG", "/usr/bin/ffmpeg")
SENDMAIL = os.path.join(BASE, "tools", "send_mail.py")

# ---------------------------------------------------------------- 邮件
SMTP_HOST = _g("SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(_g("SMTP_PORT", "465"))
SMTP_USER = _g("SMTP_USER")
SMTP_PASS = _g("SMTP_PASS")

# ---------------------------------------------------------------- 大模型 / 语音
LLM_BASE = _g("LLM_BASE", "https://api.deepseek.com/v1")
LLM_KEY = _g("LLM_KEY")
LLM_MODEL = _g("LLM_MODEL", "deepseek-chat")
VOLC_KEY = _g("VOLC_KEY")          # 火山语音（可选）
VOICE_ID = _g("VOICE_ID")          # 复刻音色 ID（可选）

# ---------------------------------------------------------------- 实时通话（可选）
TRTC_APPID = _g("TRTC_APPID")
TRTC_KEY = _g("TRTC_KEY")


def u(path):
    """拼成绝对地址，例如 u('/xin/art') -> https://你的域名/xin/art"""
    if not path.startswith("/"):
        path = "/" + path
    return SITE + path
