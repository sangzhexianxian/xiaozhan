"""聊天记录到期自动清（默认 60 天，环境变量 XIN_KEEP_DAYS 可改）"""
import os
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

DAYS = int(os.environ.get("XIN_KEEP_DAYS", "60"))
cut = time.strftime("%Y-%m-%d %H:%M:%S",
                    time.localtime(time.time() - DAYS * 86400))

c = sqlite3.connect(core.DB)
n1 = c.execute("SELECT COUNT(*) FROM chat WHERE created < ?", (cut,)).fetchone()[0]
c.execute("DELETE FROM chat WHERE created < ?", (cut,))

# 已经交付完的信，正文也一起清掉（只留骨架）
n2 = 0
try:
    rows = c.execute("""SELECT id FROM threads WHERE status IN ('paid','done')
                        AND created < ? AND COALESCE(note,'')<>''""", (cut,)).fetchall()
    for r in rows:
        c.execute("UPDATE threads SET note='[已按期限清理]' WHERE id=?", (r[0],))
        n2 += 1
except Exception:
    pass

c.commit()
c.close()
print("%s 清了 %d 条对话、%d 封信正文（保留 %d 天）"
      % (time.strftime("%Y-%m-%d %H:%M"), n1, n2, DAYS))
