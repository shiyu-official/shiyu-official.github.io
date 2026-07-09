#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ドーミーイン系＋共立リゾートのマスター（全店リスト）を生成し data/dormy_master.json を出力する。
あわせて、店舗名の表記ゆれ事故を防ぐため、Issueフォームの店舗ドロップダウン
（.github/ISSUE_TEMPLATE/dormy-visit.yml）をマスターから再生成する。

データ源（いずれか）:
  1) Wikipedia（MediaWiki API・生wikitext）… 既定。
       - 記事「ドーミーイン」  … dormy型（温泉名 店舗名（所在）／店名からブランド推定）
       - 記事「共立リゾート」    … resort型（宿名（都道府県/温泉地）／全て brand=resort）
  2) ローカル貼付け data/dormy_wiki_raw.txt … 存在すれば dormy型として優先解析（手動フォールバック）。

各ホテル: { id, name, onsen, pref, region, brand }
  brand: nono / premium / express / resort / dormy
踏破率の分母は既定でマスター件数。meta.totalPin に数値を入れると固定（前回値を保持）。
"""
import json, os, re, sys, hashlib, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "dormy_master.json")
RAW = os.path.join(DATA, "dormy_wiki_raw.txt")          # 記事「ドーミーイン」の貼付け（dormy型）
RAW_RESORT = os.path.join(DATA, "dormy_kyoritsu_raw.txt")  # 記事「共立リゾート」の貼付け（resort型）
ISSUE_TPL = os.path.join(ROOT, ".github", "ISSUE_TEMPLATE", "dormy-visit.yml")
BULK_TPL = os.path.join(ROOT, ".github", "ISSUE_TEMPLATE", "dormy-visit-bulk.yml")

WIKI_SOURCES = [
    {"title": "ドーミーイン", "mode": "dormy"},
    {"title": "共立リゾート", "mode": "resort"},
]
UA = "shiyu-station-dormy-bot/1.0 (https://shiyu-official.github.io)"

PREF2REGION = {
    "北海道": "北海道",
    "青森県": "東北", "岩手県": "東北", "宮城県": "東北", "秋田県": "東北", "山形県": "東北", "福島県": "東北",
    "茨城県": "関東", "栃木県": "関東", "群馬県": "関東", "埼玉県": "関東", "千葉県": "関東", "東京都": "関東", "神奈川県": "関東",
    "新潟県": "甲信越", "長野県": "甲信越", "山梨県": "甲信越",
    "富山県": "北陸", "石川県": "北陸", "福井県": "北陸",
    "岐阜県": "東海", "静岡県": "東海", "愛知県": "東海", "三重県": "東海",
    "滋賀県": "近畿", "京都府": "近畿", "大阪府": "近畿", "兵庫県": "近畿", "奈良県": "近畿", "和歌山県": "近畿",
    "鳥取県": "中国", "島根県": "中国", "岡山県": "中国", "広島県": "中国", "山口県": "中国",
    "徳島県": "四国", "香川県": "四国", "愛媛県": "四国", "高知県": "四国",
    "福岡県": "九州", "佐賀県": "九州", "長崎県": "九州", "熊本県": "九州", "大分県": "九州", "宮崎県": "九州", "鹿児島県": "九州", "沖縄県": "九州",
}
PREFS = list(PREF2REGION.keys())
REGION_ORDER = ["北海道", "東北", "関東", "甲信越", "北陸", "東海", "近畿", "中国", "四国", "九州"]
BRAND_ORDER = {"dormy": 0, "premium": 0, "express": 0, "nono": 1, "resort": 2}
EXCLUDE = ("閉館", "休業", "休館", "現:アパホテル", "現：アパホテル")

# Wikipedia「ドーミーイン」記事にも公式リストにも未掲載の実在店を手動補完する。
# 取得元が更新されても消えないよう、毎回このリストをマージする（dedupeで重複排除）。
# 例）{"name":"ドーミーイン◯◯","onsen":"天然温泉 ◯◯の湯","pref":"◯◯県","region":"◯◯","brand":"dormy"}
# ※津・和歌山は記事本文に載っているため、貼付け／APIから自動取得される（ここには不要）。
MANUAL_ADD = []


def fetch_wikitext(title):
    api = "https://ja.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "prop": "revisions", "titles": title,
        "rvslots": "main", "rvprop": "content", "formatversion": "2",
        "format": "json", "redirects": "1",
    })
    req = urllib.request.Request(api, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    for p in data.get("query", {}).get("pages", []):
        for rev in p.get("revisions", []):
            return rev.get("slots", {}).get("main", {}).get("content", "") or ""
    return ""


def strip_markup(s):
    s = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"\[\d+\]", "", s)
    s = re.sub(r"''+", "", s)
    return s


def mkid(name):
    return "d" + hashlib.md5(name.encode("utf-8")).hexdigest()[:8]


def brand_from_name(name):
    if "野乃" in name:
        return "nono"
    if "PREMIUM" in name.upper():
        return "premium"
    if "EXPRESS" in name.upper():
        return "express"
    return "dormy"


def pref_in(text):
    for pf in PREFS:
        if pf in text:
            return pf
    return ""


def parse_dormy(text):
    hotels = []
    # 記事内の節見出しでブランドを判定する（例：ラビスタ富良野ヒルズはPREMIUM節）。
    # 見出しが取れないときは店名キーワードにフォールバック。
    SECTION_BRANDS = {
        "ドーミーインPREMIUM": "premium",
        "御宿 野乃": "nono", "御宿野乃": "nono",
        "ドーミーインEXPRESS": "express",
    }
    section_brand = ""   # 空 = ドーミーイン本体（dormy）
    for raw in text.splitlines():
        line = strip_markup(raw).strip().lstrip("*-・ 　\t")
        if not line or "==" in line:
            continue
        # 節見出し行ならブランドを切り替えて次へ（店舗行ではない）
        if line in SECTION_BRANDS:
            section_brand = SECTION_BRANDS[line]
            continue
        if not any(k in line for k in ("ドーミーイン", "御宿", "ラビスタ")):
            continue
        if any(x in line for x in EXCLUDE):
            continue
        pref = pref_in(line)
        if not pref:
            continue
        ns = -1
        for kw in ("ドーミーイン", "御宿", "ラビスタ"):
            i = line.find(kw)
            if i >= 0 and (ns < 0 or i < ns):
                ns = i
        if ns < 0:
            continue
        onsen = line[:ns].strip(" 　-・")
        rest = line[ns:]
        name = re.sub(r"\s+", " ", re.split(r"[（(]", rest, maxsplit=1)[0]).strip()
        name = re.split(r"※|旧", name)[0].strip()
        if not any(k in name for k in ("ドーミーイン", "野乃", "ラビスタ")):
            continue
        # ブランド＝節見出し優先。見出し不明時は店名から推定。
        brand = section_brand or brand_from_name(name)
        hotels.append({
            "name": name,
            "onsen": onsen if ("湯" in onsen or "温泉" in onsen) else "",
            "pref": pref, "region": PREF2REGION.get(pref, ""),
            "brand": brand,
        })
    return hotels


def parse_resort(text):
    hotels = []
    for raw in text.splitlines():
        line = strip_markup(raw).strip().lstrip("*-・ 　\t")
        if not line or "==" in line:
            continue
        if any(x in line for x in EXCLUDE):
            continue
        m = re.search(r"[（(]([^）)]*)[）)]", line)   # （都道府県/温泉地）
        if not m:
            continue
        pref = pref_in(m.group(1))
        if not pref:
            continue
        name = re.sub(r"\s+", " ", line[:m.start()]).strip(" 　-・")
        if not name or len(name) < 2:
            continue
        hotels.append({
            "name": name, "onsen": "",
            "pref": pref, "region": PREF2REGION.get(pref, ""),
            "brand": "resort",
        })
    return hotels


def dedupe(hotels):
    out, seen = [], set()
    for h in hotels:
        if h["name"] in seen:
            continue
        seen.add(h["name"])
        h["id"] = mkid(h["name"])
        out.append(h)
    return out


def _sorted_names(hotels):
    def sortkey(h):
        return (BRAND_ORDER.get(h["brand"], 9),
                REGION_ORDER.index(h["region"]) if h["region"] in REGION_ORDER else 99,
                h["name"])
    return [h["name"] for h in sorted(hotels, key=sortkey)]


def write_issue_template(hotels):
    """マスターの店舗名でIssueフォームの店舗ドロップダウンを再生成（表記ゆれ防止）。"""
    opts = "\n".join("        - %s" % n for n in _sorted_names(hotels))
    tpl = """name: ドーミーイン宿泊を追加
description: 泊まったドーミーインを写真つきで記録します（スマホからでOK）
title: "[dormy] "
labels: ["dormy-visit"]
body:
  - type: dropdown
    id: hotel
    attributes:
      label: 店舗名
      description: "マスターから選択（表記ゆれ防止）。一覧に無い新店は本文に手入力でも可。"
      options:
%s
    validations:
      required: true
  - type: input
    id: firstvisit
    attributes:
      label: 初宿泊日
      description: "YYYY-MM-DD 形式"
      placeholder: "2024-10-02"
  - type: input
    id: nights
    attributes:
      label: 延べ泊数
      description: "これまでの合計泊数（数字）"
      placeholder: "1"
  - type: textarea
    id: photo
    attributes:
      label: 写真
      description: "この枠に写真を1枚ドラッグ＆ドロップ（スマホはタップして画像を添付）。自分で撮った写真のみ。"
      placeholder: ここに画像を貼り付け
""" % opts
    os.makedirs(os.path.dirname(ISSUE_TPL), exist_ok=True)
    open(ISSUE_TPL, "w", encoding="utf-8").write(tpl)


def write_bulk_template(hotels):
    """まとめ投稿フォームを再生成。記入例の下に、コピペ用の店舗名一覧（折りたたみ）を埋め込む。"""
    listing = "\n".join("        " + n for n in _sorted_names(hotels))
    tpl = """name: ドーミーイン宿泊をまとめて追加
description: 複数の宿泊を1回でまとめて記録します（各行に写真1枚をドロップ）
title: "[dormy] まとめて追加"
labels: ["dormy-visit"]
body:
  - type: markdown
    attributes:
      value: |
        **1行1件**で入力してください。書式：
        `店舗名 / 初宿泊日(YYYY-MM-DD) / 泊数`
        各行の**末尾にその宿の写真を1枚ドラッグ＆ドロップ**（写真は任意）。
        **改行で1件区切り**（画面幅による折り返しは見た目だけで、登録に影響しません）。
        店舗名はマスター表記に合わせて（多少のゆれは自動吸収）。突合できない行は結果コメントで知らせます。
        例）
        ```
        ドーミーイン札幌ANNEX / 2024-10-02 / 3  ![写真]
        御宿 野乃 浅草 / 2025-03-15 / 2  ![写真]
        ```
        <details><summary>店舗名一覧（コピペ用・タップで開閉）</summary>

        ```
%s
        ```

        </details>
  - type: textarea
    id: bulk
    attributes:
      label: 宿泊記録
      description: "1行1件（店舗名 / 初宿泊日 / 泊数）。各行末に写真1枚をドロップ。"
      placeholder: |
        ドーミーイン札幌ANNEX / 2024-10-02 / 3
        御宿 野乃 浅草 / 2025-03-15 / 2
    validations:
      required: true
""" % listing
    os.makedirs(os.path.dirname(BULK_TPL), exist_ok=True)
    open(BULK_TPL, "w", encoding="utf-8").write(tpl)


def load_prev_meta():
    if os.path.exists(OUT):
        try:
            return json.load(open(OUT, encoding="utf-8")).get("meta", {})
        except Exception:
            pass
    return {}


def main():
    hotels = []
    srcs = []

    # --- ドーミーイン（dormy／PREMIUM／EXPRESS／御宿野乃）---
    if os.path.exists(RAW):
        hotels += parse_dormy(open(RAW, encoding="utf-8-sig", errors="replace").read())
        srcs.append("ドーミーイン=貼付け")
    else:
        try:
            hotels += parse_dormy(fetch_wikitext("ドーミーイン"))
            srcs.append("ドーミーイン=API")
        except Exception as e:
            sys.stderr.write("[build_dormy_master] 取得失敗 ドーミーイン: %s\n" % e)

    # --- 共立リゾート（resort）---
    if os.path.exists(RAW_RESORT):
        hotels += parse_resort(open(RAW_RESORT, encoding="utf-8-sig", errors="replace").read())
        srcs.append("共立リゾート=貼付け")
    else:
        try:
            hotels += parse_resort(fetch_wikitext("共立リゾート"))
            srcs.append("共立リゾート=API")
        except Exception as e:
            sys.stderr.write("[build_dormy_master] 取得失敗 共立リゾート: %s\n" % e)

    src = "Wikipedia（%s）" % "・".join(srcs)

    # 記事に載らない実在店を補完（dedupeで重複排除）
    hotels += [dict(h) for h in MANUAL_ADD]
    hotels = dedupe(hotels)
    if not hotels:
        sys.stderr.write("[build_dormy_master] ホテルを抽出できませんでした。\n")
        return

    prev = load_prev_meta()
    jst = timezone(timedelta(hours=9))
    meta = {
        "source": src,
        "asOf": datetime.now(jst).strftime("%Y-%m"),
        "scope": "ドーミーイン・御宿野乃＋共立リゾート系",
        "note": "build_dormy_master.py が生成。totalPin に数値を入れると踏破率の分母を固定できる。",
        "totalPin": prev.get("totalPin"),
    }
    json.dump({"meta": meta, "hotels": hotels}, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    write_issue_template(hotels)
    write_bulk_template(hotels)

    from collections import Counter
    c = Counter(h["brand"] for h in hotels)
    print("[build_dormy_master] wrote %s（%d 施設）%s" % (OUT, len(hotels), dict(c)))
    print("[build_dormy_master] issue template updated（%d 店舗をドロップダウン化）" % len(hotels))


if __name__ == "__main__":
    main()
