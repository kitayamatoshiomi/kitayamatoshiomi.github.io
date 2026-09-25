"""Obsidian 保管庫のテーマ別ノート本数を data/obsidian.json に書き出す。

保管庫はローカル（＋非公開リポジトリ）にあるので、GitHub Actions では動かせない。
このPCで `py scripts/obsidian_count.py` を実行したときだけ更新される。
書き出すのは件数だけで、ノートの題名や中身は一切含めない。
"""
import json
import os
from datetime import datetime, timedelta, timezone

VAULT = os.environ.get("VAULT", r"C:\Users\nakam\Desktop\Obisidian用フォルダ")
HUBS = [("執筆", "#5cb6b3"), ("ふりかえり", "#b48ead"), ("読書メモ", "#d9a441"), ("日常メモ", "#8fbf72")]
SKIP = (".git", ".obsidian", ".trash")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JST = timezone(timedelta(hours=9))


def notes():
    for base, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(base, f), f[:-3]


def main():
    counts = {h: 0 for h, _ in HUBS}
    total = 0
    for path, name in notes():
        total += 1
        if name in counts:                      # ハブノート自身は数えない
            continue
        try:
            with open(path, encoding="utf-8", errors="ignore") as fp:
                text = fp.read()
        except Exception:
            continue
        folder = os.path.basename(os.path.dirname(path))
        for h, _ in HUBS:
            if ("[[%s]]" % h) in text or folder == h:
                counts[h] += 1
                break
    out = {"updated": datetime.now(JST).isoformat(), "total": total,
           "items": [{"name": h, "col": c, "count": counts[h]} for h, c in HUBS],
           "vault": os.path.basename(VAULT)}
    with open(os.path.join(ROOT, "data", "obsidian.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("obsidian:", total, counts)


if __name__ == "__main__":
    main()
