# -*- coding: utf-8 -*-
"""内容留意词：命中就给两边都提个醒（不拦截，只标出来）"""
import re

# 分成几类，各自给不同的提示
GROUPS = [
    ("self", "可能伤到自己",
     ["自杀", "轻生", "不想活", "活不下去", "了结", "结束生命", "割腕", "跳楼", "安眠药",
      "想死", "死了算了", "没意思活", "烧炭", "上吊"]),
    ("violence", "涉及伤害他人",
     ["杀了他", "杀死", "砍死", "报复他", "弄死", "下毒", "找人打"]),
    ("money", "涉及转账汇款",
     ["转账", "汇款", "银行卡号", "验证码", "投资", "刷单", "返利", "博彩", "赌"]),
    ("adult", "涉及成人内容",
     ["裸聊", "约炮", "色情", "开房", "包养"]),
    ("abuse", "用了重话",
     ["去死", "废物", "垃圾人", "畜生", "傻逼"]),
]

# 这些词单字也要小心，避免"杀死时间"这类误伤，做简单排除
SAFE = ["杀死时间", "杀死比赛", "杀死寂寞", "想死你了", "笑死", "累死", "热死", "饿死"]


def scan(text):
    """返回 [(类名, 中文说明, 命中的词), ...]"""
    if not text:
        return []
    t = text.replace(" ", "")
    for s in SAFE:
        t = t.replace(s, "＿")
    out = []
    for code, label, words in GROUPS:
        hit = [w for w in words if w in t]
        if hit:
            out.append((code, label, hit[:3]))
    return out


def brief(text):
    """一句话结论，没有就是空串"""
    r = scan(text)
    if not r:
        return ""
    return "、".join([x[1] for x in r])


def words(text):
    r = scan(text)
    seen = []
    for _c, _l, ws in r:
        seen.extend(ws)
    return seen
