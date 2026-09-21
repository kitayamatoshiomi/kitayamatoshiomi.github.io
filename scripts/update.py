"""Work Base のデータ更新スクリプト（GitHub Actions から毎時実行）。

- data/news.json   : 教育・出版のニュース（Google ニュース RSS）
- data/notion.json : Notion「今週の作業板」の完了済み件数（NOTION_TOKEN があるときだけ更新）

標準ライブラリのみ。ローカルでも `python scripts/update.py` で動く。
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
JST = timezone(timedelta(hours=9))
NOW = datetime.now(JST)

# ---------------------------------------------------------------- news
NEWS_QUERIES = {
    # 教育：専門媒体を軸に、一般紙の文科省まわりで補う
    "edu": ["site:kyobun.co.jp when:5d", "site:resemom.jp when:2d",
            "site:kyoiku-press.com when:7d", "文部科学省 OR 中教審 when:1d"],
    # 出版：業界紙（新文化・文化通信・HON.jp）＋一般ニュース
    "pub": ["site:shinbunka.co.jp when:7d", "site:bunkanews.jp when:7d",
            "site:hon.jp when:7d", "出版社 OR 書店 OR 出版業界 when:2d"],
}
BLOCK_SOURCES = ("Vietnam.vn", "TVer", "YouTube", "Межа", "選挙ドットコム", "ニコニコニュース", "fujitv",
                 "食品新聞", "ねとらぼ", "企業調査", "蔦屋書店ポータル", "ラノベニュース")
BLOCK_TITLE = re.compile(r"^\d{4}年\d{1,2}月\d{1,2}日$|Archives|お休みします|^画像")
PER_SOURCE = 7
NEWS_MAX = 18


def fetch(url, headers=None, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={
        "User-Agent": "Mozilla/5.0 (WorkBase updater)", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def news_for(q):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q, "hl": "ja", "gl": "JP", "ceid": "JP:ja"})
    root = ET.fromstring(fetch(url))
    out, seen = [], set()
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        src_el = it.find("source")
        source = (src_el.text or "").strip() if src_el is not None else ""
        if source and title.endswith(" - " + source):
            title = title[: -len(" - " + source)]
        key = re.sub(r"\s+", "", title)[:40]
        if not title or key in seen:
            continue
        seen.add(key)
        try:
            ts = parsedate_to_datetime(it.findtext("pubDate")).astimezone(JST).isoformat()
        except Exception:
            ts = None
        out.append({"title": title, "url": (it.findtext("link") or "").strip(),
                    "source": source, "time": ts})
    out.sort(key=lambda x: x["time"] or "", reverse=True)
    return out[:NEWS_MAX]


def update_news():
    res = {"updated": NOW.isoformat()}
    prev = load("news.json")
    for k, qs in NEWS_QUERIES.items():
        pool, ok = [], False
        for q in qs:
            try:
                pool += news_for(q); ok = True
            except Exception as e:
                print("news", q, "failed:", e, file=sys.stderr)
        if not ok:  # 全滅なら前回分を残す
            res[k] = prev.get(k, []); continue
        pool.sort(key=lambda x: x["time"] or "", reverse=True)
        out, seen, per = [], set(), {}
        for x in pool:
            key = re.sub(r"\W", "", x["title"])[:22]
            if key in seen or any(b in x["source"] for b in BLOCK_SOURCES) or BLOCK_TITLE.search(x["title"]):
                continue
            if per.get(x["source"], 0) >= PER_SOURCE:
                continue
            seen.add(key); per[x["source"]] = per.get(x["source"], 0) + 1
            out.append(x)
        res[k] = out[:NEWS_MAX]
    save("news.json", res)
    print("news:", {k: len(v) for k, v in res.items() if isinstance(v, list)})


# ---------------------------------------------------------------- notion
NOTION_PAGE = os.environ.get("NOTION_PAGE", "32667766d902813fb566d2e6d8d9513f")


def notion_children(block_id, token):
    items, cursor = [], None
    while True:
        url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
        if cursor:
            url += "&start_cursor=" + cursor
        j = json.loads(fetch(url, {"Authorization": "Bearer " + token,
                                   "Notion-Version": "2022-06-28"}))
        items += j.get("results", [])
        if not j.get("has_more"):
            return items
        cursor = j.get("next_cursor")


def plain(block):
    body = block.get(block.get("type"), {}) or {}
    return "".join(t.get("plain_text", "") for t in body.get("rich_text", []))


def update_notion():
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print("notion: NOTION_TOKEN なし → スキップ")
        return
    blocks = notion_children(NOTION_PAGE, token)
    done, today, section = None, 0, ""
    for b in blocks:
        t = b.get("type", "")
        text = plain(b)
        if t.startswith("heading_"):
            section = text
        if "完了済み" in text and (t == "toggle" or b.get("has_children")):
            kids = notion_children(b["id"], token)
            done = sum(1 for k in kids if plain(k).strip())
            section = ""
            continue
        if "今日やること" in section and t in ("bulleted_list_item", "to_do", "numbered_list_item") and text.strip():
            today += 1
    if done is None:
        print("notion: 「完了済み」ブロックが見つからない", file=sys.stderr)
        return
    prev = load("notion.json")
    hist = prev.get("history", {})
    hist[NOW.strftime("%Y-%m-%d")] = done
    hist = dict(sorted(hist.items())[-90:])
    save("notion.json", {"updated": NOW.isoformat(), "done": done, "today": today,
                         "history": hist, "url": prev.get("url")})
    print("notion: done", done, "today", today)


# ---------------------------------------------------------------- io
def load(name):
    try:
        with open(os.path.join(DATA, name), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save(name, obj):
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    update_news()
    try:
        update_notion()
    except Exception as e:
        print("notion failed:", e, file=sys.stderr)
