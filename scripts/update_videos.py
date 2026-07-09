#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-志遊- shiyu's station ｜ 動画・お知らせ自動更新スクリプト（標準ライブラリのみ）

やること
  1. 各YouTubeチャンネルのRSSから最新動画を取得
  2. index.html の AUTO:LATEST 区間を「最新動画カルーセル」に更新
  3. AUTO:RAIL / AUTO:TAIKO の代表動画タイトルを oEmbed で更新
  4. 新着動画・新規ブログ記事を検知し、定型文で AUTO:NEWS 区間に追記
  5. 状態（既知ID・お知らせ履歴）を data/last_seen.json に保存

初回実行では既存の動画を一括で「新着」通知しないよう、IDのシードのみ行います。
"""

import json
import os
import re
import sys
import html
import urllib.request
import urllib.parse
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
UA = "Mozilla/5.0 (compatible; shiyu-site-updater/1.0; +https://shiyu-official.github.io)"

YT_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


# ---------- 入出力ユーティリティ ----------
def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def http_get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.read().decode("utf-8", "replace")


# ---------- YouTube 取得 ----------
def resolve_channel_id(handle_or_id):
    """@handle または UC... からチャンネルIDを解決。"""
    if handle_or_id.startswith("UC") and len(handle_or_id) == 24:
        return handle_or_id
    handle = handle_or_id.lstrip("/")
    url = "https://www.youtube.com/%s" % urllib.parse.quote(handle)
    try:
        page = http_get(url)
    except Exception as e:
        print("  ! channel page fetch failed (%s): %s" % (handle, e))
        return None
    for pat in (r'"channelId":"(UC[0-9A-Za-z_-]{22})"',
                r'"externalId":"(UC[0-9A-Za-z_-]{22})"',
                r'youtube\.com/channel/(UC[0-9A-Za-z_-]{22})'):
        m = re.search(pat, page)
        if m:
            return m.group(1)
    print("  ! channelId not found for", handle)
    return None


def fetch_rss(channel_id):
    """チャンネルRSSを取得し新しい順の動画リストを返す。"""
    url = "https://www.youtube.com/feeds/videos.xml?channel_id=%s" % channel_id
    xml = http_get(url)
    root = ET.fromstring(xml)
    items = []
    for entry in root.findall("atom:entry", YT_NS):
        vid = entry.findtext("yt:videoId", default="", namespaces=YT_NS)
        title = entry.findtext("atom:title", default="", namespaces=YT_NS)
        published = entry.findtext("atom:published", default="", namespaces=YT_NS)
        if not vid:
            continue
        items.append({"id": vid, "title": title, "published": published})
    return items


def fetch_oembed_title(video_url):
    api = "https://www.youtube.com/oembed?url=%s&format=json" % urllib.parse.quote(video_url, safe="")
    try:
        data = json.loads(http_get(api, timeout=15))
        return data.get("title")
    except Exception as e:
        print("  ! oEmbed failed for %s: %s" % (video_url, e))
        return None


# ---------- 日付 ----------
def parse_dt(s):
    if not s:
        return datetime.now(timezone.utc)
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return datetime.now(timezone.utc)


def fmt_date(dt):
    return dt.astimezone(timezone.utc).strftime("%Y.%m.%d")


def video_id_from_url(url):
    m = re.search(r"(?:youtu\.be/|v=|/embed/)([0-9A-Za-z_-]{6,})", url)
    return m.group(1) if m else url


# ---------- HTML 生成 ----------
def esc(s):
    return html.escape(s or "", quote=True)


def latest_card_html(v):
    thumb = "https://i.ytimg.com/vi/%s/hqdefault.jpg" % v["id"]
    watch = "https://youtu.be/%s" % v["id"]
    return (
        '          <a class="card" href="%s" target="_blank" rel="noopener">\n'
        '            <div class="card__thumb"><span class="badge">%s</span>'
        '<span class="play"><i class="fa-brands fa-youtube"></i></span>'
        '<img src="%s" alt="" loading="lazy"></div>\n'
        '            <p class="card__title">%s</p>\n'
        '            <p class="card__meta">%s</p>\n'
        '          </a>\n'
        % (esc(watch), esc(v["badge"]), esc(thumb), esc(v["title"]), esc(v.get("category") or v["channel_name"]))
    )


def rep_card_html(item, title):
    vid = video_id_from_url(item["url"])
    thumb = "https://i.ytimg.com/vi/%s/hqdefault.jpg" % vid
    label = title if title else "▶ YouTube で見る"
    return (
        '          <a class="card inview" href="%s" target="_blank" rel="noopener">\n'
        '            <div class="card__thumb"><span class="play"><i class="fa-brands fa-youtube"></i></span>'
        '<img src="%s" alt="" loading="lazy"></div>\n'
        '            <p class="card__title" data-vid="%s">%s</p>\n'
        '          </a>\n'
        % (esc(item["url"]), esc(thumb), esc(vid), esc(label))
    )


def news_item_html(n):
    tagcls = "tag tag--new" if n.get("new") else "tag"
    return (
        '          <div>\n'
        '            <dt>%s</dt>\n'
        '            <span class="%s">%s</span>\n'
        '            <dd>%s</dd>\n'
        '          </div>\n'
        % (esc(n["date"]), tagcls, esc(n["tag"]), esc(n["text"]))
    )


def replace_region(html_text, name, inner):
    pat = re.compile(r"(<!-- AUTO:%s:START.*?-->)(.*?)(<!-- AUTO:%s:END -->)" % (name, name), re.S)
    if not pat.search(html_text):
        print("  ! marker not found:", name)
        return html_text
    return pat.sub(lambda m: m.group(1) + "\n" + inner + "        " + m.group(3), html_text)


# ---------- メイン ----------
def main():
    cfg = load_json(os.path.join(DATA, "videos.json"))
    if not cfg:
        print("videos.json missing"); return 0
    state = load_json(os.path.join(DATA, "last_seen.json"),
                      {"initialized": False, "videos": {"rail": [], "taiko": []}, "blog": [], "news": []})
    state.setdefault("videos", {})
    state.setdefault("blog", [])
    state.setdefault("news", [])
    blog = load_json(os.path.join(DATA, "blog.json"), {"posts": []})

    index_path = os.path.join(ROOT, cfg.get("index_file", "index.html"))
    page = open(index_path, encoding="utf-8").read()
    original = page

    all_latest = []          # 最新動画（両ch混合）
    new_events = []          # 今回検知した新着（動画・ブログ）
    first_run = not state.get("initialized")

    # --- 各チャンネル：RSS取得 → 最新収集 & 新着検知 ---
    for key, ch in cfg["channels"].items():
        cid = ch.get("channel_id") or resolve_channel_id(ch["handle"])
        if not cid:
            continue
        try:
            items = fetch_rss(cid)
        except Exception as e:
            print("  ! RSS failed (%s): %s" % (key, e))
            continue
        seen = set(state["videos"].get(key, []))
        for v in items:
            v["channel_key"] = key
            v["badge"] = ch.get("badge", "")
            v["channel_name"] = ch.get("name", "")
            v["category"] = ch.get("category", "")
            v["dt"] = parse_dt(v["published"])
            all_latest.append(v)
            if v["id"] not in seen and not first_run:
                new_events.append({
                    "date": fmt_date(v["dt"]),
                    "tag": "新着動画", "new": True,
                    "text": cfg["news_templates"]["video"].format(channel=ch.get("name", ""), title=v["title"]),
                    "dt": v["dt"],
                })
        # 状態更新（既知IDを最新のRSSで置き換え）
        state["videos"][key] = [v["id"] for v in items] or list(seen)

    # --- 最新動画カルーセルを更新 ---
    if all_latest:
        all_latest.sort(key=lambda x: x["dt"], reverse=True)
        top = all_latest[: cfg.get("latest_count", 8)]
        inner = "".join(latest_card_html(v) for v in top)
        page = replace_region(page, "LATEST",
                              '        <div class="list1 list-auto">\n' + inner + '        </div>\n')

    # --- 代表動画タイトルを oEmbed で更新 ---
    for key, region in (("rail", "RAIL"), ("taiko", "TAIKO")):
        reps = cfg.get("representative", {}).get(key, [])
        if not reps:
            continue
        cards = ""
        for item in reps:
            title = fetch_oembed_title(item["url"])
            cards += rep_card_html(item, title)
        page = replace_region(page, region, '        <div class="list1">\n' + cards + '        </div>\n')

    # --- ブログ新着検知 ---
    known_blog = set(state.get("blog", []))
    for post in blog.get("posts", []):
        pid = str(post.get("id"))
        if pid and pid not in known_blog:
            if not first_run:
                pd = post.get("date", "")
                try:
                    dt = parse_dt(pd + "T00:00:00+00:00") if re.match(r"^\d{4}-\d{2}-\d{2}$", pd) else datetime.now(timezone.utc)
                except Exception:
                    dt = datetime.now(timezone.utc)
                new_events.append({
                    "date": pd.replace("-", ".") if pd else fmt_date(dt),
                    "tag": "ブログ", "new": True,
                    "text": cfg["news_templates"]["blog"].format(title=post.get("title", "")),
                    "dt": dt,
                })
    state["blog"] = [str(p.get("id")) for p in blog.get("posts", [])] or list(known_blog)

    # --- お知らせ履歴をマージ（新しい順・上限） ---
    if new_events:
        new_events.sort(key=lambda x: x.get("dt", datetime.now(timezone.utc)), reverse=True)
        merged = [{k: e[k] for k in ("date", "tag", "new", "text")} for e in new_events] + state.get("news", [])
        # 直近の「新着」ラベルは最新のみ強調、古いものは通常タグに落ち着かせる
        state["news"] = merged[: cfg.get("news_max", 5)]

    # AUTO:NEWS 区間は常に state["news"] から描画（空なら空に）
    news_inner = "".join(news_item_html(n) for n in state.get("news", []))
    page = replace_region(page, "NEWS", news_inner if news_inner else "")

    state["initialized"] = True
    save_json(os.path.join(DATA, "last_seen.json"), state)

    if page != original:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(page)
        print("index.html updated.")
    else:
        print("no HTML changes.")
    if first_run:
        print("first run: seeded IDs without flooding news.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
