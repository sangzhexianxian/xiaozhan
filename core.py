# -*- coding: utf-8 -*-
"""小站的信 · 核心：数据库 / AI 出稿 / 音频合成"""
import json
import os
import random
import re
import sqlite3
import string
import subprocess
import time
import urllib.request
import conf

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
MEDIA = os.path.join(BASE, "media")
DB = os.path.join(DATA, "letters.db")
FFMPEG = conf.FFMPEG
APP_DB = os.environ.get("APP_DB", "")

os.makedirs(DATA, exist_ok=True)
os.makedirs(MEDIA, exist_ok=True)


# ---------------------------------------------------------------- 数据库
def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    c = conn()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS threads (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          kind TEXT NOT NULL,            -- reply | read
          price INTEGER DEFAULT 0,
          status TEXT DEFAULT 'pending', -- pending | paid | done | rejected
          nick TEXT DEFAULT '',
          contact TEXT DEFAULT '',
          note TEXT DEFAULT '',          -- 客户原话 / 文稿
          req  TEXT DEFAULT '',          -- 代读要求（语气、用途）
          tier TEXT DEFAULT '',          -- 代读档位
          audio_in TEXT DEFAULT '',      -- 客户语音
          draft TEXT DEFAULT '',
          final_text TEXT DEFAULT '',
          audio_out TEXT DEFAULT '',
          token TEXT DEFAULT '',
          created TEXT,
          paid_at TEXT DEFAULT '',
          done_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);
        """
    )
    c.commit()
    # 默认配置
    for k, v in {
        "brand": "我的小站",
        "sub": "有些话，说不出口的，写在这里",
        "persona": "你是一位做了很多年的创作者，靠作品被人记住。",
        "desk_key": "",
        "ops_key": "",
        "price_reply": "99",
        "price_r1": "39",
        "price_r2": "69",
        "price_r3": "99",
        "paused": "0",
    }.items():
        c.execute("INSERT OR IGNORE INTO kv(k,v) VALUES(?,?)", (k, v))
    c.commit()
    # 生成工作台密钥
    key = get("desk_key")
    if not key:
        key = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
        set("desk_key", key)
    okey = get("ops_key")
    if not okey:
        okey = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
        set("ops_key", okey)
    c.close()
    return key


def get(k, d=""):
    c = conn()
    r = c.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
    c.close()
    return r["v"] if r else d


def set(k, v):
    c = conn()
    c.execute("INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, str(v)))
    c.commit()
    c.close()


def q(sql, args=()):
    c = conn()
    rows = c.execute(sql, args).fetchall()
    c.close()
    return [dict(r) for r in rows]


def one(sql, args=()):
    r = q(sql, args)
    return r[0] if r else None


def ex(sql, args=()):
    c = conn()
    cur = c.execute(sql, args)
    c.commit()
    rid = cur.lastrowid
    c.close()
    return rid


def new_token(n=6):
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    c = conn()
    for _ in range(20):
        t = "".join(random.choice(alphabet) for _ in range(n))
        if not c.execute("SELECT 1 FROM threads WHERE token=?", (t,)).fetchone():
            c.close()
            return t
    c.close()
    return "".join(random.choice(alphabet) for _ in range(8))


# ---------------------------------------------------------------- AI
def _llm_conf():
    """优先 .env / 环境变量；没配再看 APP_DB（兼容旧部署）"""
    if conf.LLM_KEY:
        return conf.LLM_BASE, conf.LLM_KEY, conf.LLM_MODEL
    if APP_DB:
        try:
            c = sqlite3.connect(APP_DB)
            c.row_factory = sqlite3.Row
            d = {r["k"]: r["v"] for r in c.execute("SELECT k,v FROM settings")}
            c.close()
            return (d.get("llm_base") or conf.LLM_BASE,
                    d.get("llm_key") or "",
                    d.get("llm_model") or conf.LLM_MODEL)
        except Exception:
            pass
    return conf.LLM_BASE, "", conf.LLM_MODEL


def persona():
    """人设一句话，后台可改（kv: persona）"""
    return get("persona") or "你是一位做了很多年的创作者，靠作品被人记住。"


def llm(sys_msg, user_msg, temp=0.85, max_tokens=1600, timeout=90):
    base, key, model = _llm_conf()
    if not key:
        raise RuntimeError("没有找到模型凭据")
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg},
        ],
        "temperature": temp,
        "max_tokens": max_tokens,
        "thinking": {"type": "disabled"},
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    return d["choices"][0]["message"]["content"].strip()


SYS_REPLY = """{{PERSONA}}

现在你要给一个陌生人回一封信。写信的规则：

1. 你不是心理咨询师，也不装。你就是一个过来人。
2. 先接住他说的那件事，三五句，让他知道你听懂了。不要复述他的话，要用你的话点出他没说出口的那层。
3. 然后讲一句真话。可以是你的经历，可以说"我那时候也……"，但不要编造具体的时间地点细节，只讲感受和判断。
4. 不要讲道理，不要列一二三，不要说"首先其次最后"。
5. 不要许诺。"会好的""一定能过去"这类话一句都不要。
6. 给一个很小的动作，小到今晚就能做的。比如"今晚早点关灯""明天去吃一碗热的"。
7. 结尾要轻，不要煽情收尾。可以是一句平常的话。

文风要求：
- 短句。一句一行。
- 口语，像说话，不像写文章。
- 不用书面连接词（因此、所以、然而、综上）。
- 全篇 450 到 650 字。
- 不要标题，不要落款，不要"亲爱的"之类的称呼。第一句直接进入。
- 不要用任何 emoji。

直接输出信件正文。"""

SYS_POLISH = """你在帮一位创作者修改他给陌生人写的回信。

原稿如下：
---
{draft}
---

现在按下面的要求改，其余部分尽量保持原样，只改需要改的地方：
{instr}

规则：仍然是短句、口语、不说教、不许诺、不煽情。字数控制在 450 到 650 字。
直接输出修改后的完整信件正文，不要解释。"""


def draft_reply(note, req=""):
    user = "他写来的是这些：\n\n" + note.strip()
    if req.strip():
        user += "\n\n（他另外提了一句：" + req.strip() + "）"
    return llm(SYS_REPLY.replace("{{PERSONA}}", persona()), user)


def polish(d, instr):
    return llm(SYS_POLISH.replace("{draft}", d).replace("{instr}", instr), "开始改。", temp=0.7)


# 危机词
CRISIS = [
    "不想活", "想死", "自杀", "结束生命", "结束自己", "活不下去", "没意思活",
    "伤害自己", "割腕", "跳楼", "安眠药", "了断", "轻生", "不想醒",
]


def crisis_hit(text):
    t = (text or "").replace(" ", "")
    return [w for w in CRISIS if w in t]


# ---------------------------------------------------------------- 音频
def _run(args, timeout=180):
    p = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=timeout)
    return p.returncode, p.stderr.decode("utf-8", "replace")[-800:]


def to_mp3(src, dst):
    """任意音频 → 24k 单声道 mp3"""
    rc, err = _run([FFMPEG, "-y", "-nostdin", "-i", src, "-ac", "1", "-ar", "24000",
                    "-b:a", "96k", dst])
    return rc == 0, err


def concat_mp3(parts, dst):
    """多段 mp3 拼接（带 0.35s 间隔）"""
    parts = [p for p in parts if os.path.exists(p) and os.path.getsize(p) > 1000]
    if not parts:
        return False, "没有可用的录音"
    if len(parts) == 1:
        rc, err = _run([FFMPEG, "-y", "-nostdin", "-i", parts[0], "-ac", "1", "-ar", "24000",
                        "-b:a", "96k", dst])
        return rc == 0, err
    # 生成静音间隔
    gap = os.path.join(os.path.dirname(dst), "_gap.mp3")
    _run([FFMPEG, "-y", "-nostdin", "-f", "lavfi", "-i",
          "anullsrc=r=24000:cl=mono", "-t", "0.35", "-b:a", "96k", gap])
    lst = dst + ".txt"
    with open(lst, "w") as f:
        for i, p in enumerate(parts):
            if i:
                f.write("file '%s'\n" % gap)
            f.write("file '%s'\n" % p)
    rc, err = _run([FFMPEG, "-y", "-nostdin", "-f", "concat", "-safe", "0", "-i", lst,
                    "-ac", "1", "-ar", "24000", "-b:a", "96k", dst])
    try:
        os.remove(lst)
    except Exception:
        pass
    return rc == 0, err


def dur_of(path):
    rc, out = _run([FFMPEG.replace("ffmpeg", "ffprobe"), "-v", "error", "-show_entries",
                    "format=duration", "-of", "default=nw=1:nk=1", path])
    try:
        return float(out.strip().splitlines()[-1])
    except Exception:
        return 0.0
