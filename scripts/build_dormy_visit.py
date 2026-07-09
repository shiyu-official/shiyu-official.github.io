#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issue フォーム（ドーミーイン宿泊を追加）を解析し、
data/dormy_visits.json に1件追記し、写真をサムネイル化して images/dormy/ に保存する。

使い方（Action内）:
  ISSUE_BODY 環境変数に Issue 本文を渡して実行。
  結果メッセージを標準出力（Actionがコメントに使う）。

Issue本文の想定（GitHub issue forms のレンダリング）:
  ### 店舗名
  ドーミーイン札幌ANNEX
  ### 初宿泊日
  2024-10-02
  ### 延べ泊数
  3
  ### 写真
  ![image](https://github.com/.../xxxx.jpg)

店舗名はマスター(dormy_master.json)へ突合してIDを確定（表記ゆれを吸収）。
写真は長辺800pxにリサイズし WebP 変換して images/dormy/<id>.webp に保存（軽量化）。
"""
import json, os, re, sys, io

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
IMG_DIR = os.path.join(ROOT, "images", "dormy")
MASTER = os.path.join(DATA, "dormy_master.json")
VISITS = os.path.join(DATA, "dormy_visits.json")


def parse_issue(body):
    """### ラベル\\n値 形式を辞書化。"""
    fields = {}
    cur = None
    buf = []
    for line in body.replace("\r\n", "\n").split("\n"):
        m = re.match(r"^#{2,4}\s+(.+?)\s*$", line)
        if m:
            if cur is not None:
                fields[cur] = "\n".join(buf).strip()
            cur = m.group(1).strip()
            buf = []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        fields[cur] = "\n".join(buf).strip()
    return fields


def norm(s):
    return re.sub(r"[\s　]+", "", str(s or "")).replace("・", "")


def match_hotel(name, hotels):
    n = norm(name)
    if not n:
        return None
    for h in hotels:
        if norm(h["name"]) == n:
            return h
    for h in hotels:            # 部分一致フォールバック
        if n in norm(h["name"]) or norm(h["name"]) in n:
            return h
    return None


def extract_image_url(text):
    t = text or ""
    # 1) Markdown 形式 ![alt](url)
    m = re.search(r"!\[[^\]]*\]\((https?://[^\s)]+)\)", t)
    if m:
        return m.group(1)
    # 2) HTML の <img ... src="url">（GitHubは画像を貼ると<img>で挿入する）
    m = re.search(r"""<img[^>]*\bsrc=["']?(https?://[^"'>\s]+)""", t, re.I)
    if m:
        return m.group(1)
    # 3) GitHub添付URL（拡張子なし: /user-attachments/assets/<uuid>）
    m = re.search(r"https?://github\.com/user-attachments/assets/[\w./-]+", t)
    if m:
        return m.group(0)
    # 4) 拡張子つきの直リンク
    m = re.search(r"https?://\S+\.(?:jpg|jpeg|png|webp|gif)", t, re.I)
    return m.group(0) if m else ""


def save_thumb(url, hotel_id):
    """写真をDLして長辺800pxにリサイズ保存。失敗時は None。"""
    if not url:
        return None
    try:
        import urllib.request
        from PIL import Image
        req = urllib.request.Request(url, headers={"User-Agent": "shiyu-dormy-bot/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        w, h = im.size
        m = max(w, h)
        if m > 800:
            im = im.resize((round(w * 800 / m), round(h * 800 / m)))
        os.makedirs(IMG_DIR, exist_ok=True)
        rel = os.path.join("images", "dormy", hotel_id + ".webp")
        im.save(os.path.join(ROOT, rel), "WEBP", quality=80, method=6)
        return rel.replace(os.sep, "/")
    except Exception as e:
        sys.stderr.write("[dormy_visit] 画像処理失敗: %s\n" % e)
        return None


def load_json(path, default):
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            pass
    return default


def strip_image_md(s):
    """本文から画像表現を除去（' / ' 分割を壊さないため URL 片も落とす）。"""
    s = s or ""
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)      # Markdown 画像
    s = re.sub(r"<img[^>]*>", "", s, flags=re.I)     # <img ...>
    s = re.sub(r"</?[a-zA-Z][^>]*>", "", s)          # 残った任意のHTMLタグ
    s = re.sub(r"https?://\S+", "", s)               # 生URL（添付リンク等）
    return s


def normalize_date(s):
    """2025年7月6日 / 2025/7/6 などを 2025-07-06 に正規化。読めなければ原文のまま。"""
    s = (s or "").strip()
    m = re.match(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})", s)
    if m:
        y, mo, d = (int(x) for x in m.groups())
        return "%04d-%02d-%02d" % (y, mo, d)
    return s


def process_record(name, first, nights, photo_url, hotels, visits):
    hotel = match_hotel(name, hotels)
    if not hotel:
        return ("unmatched", name)
    photo_rel = save_thumb(photo_url, hotel["id"]) if photo_url else None
    entry = {"id": hotel["id"], "name": hotel["name"]}
    first = normalize_date(first)
    if first:
        entry["firstVisit"] = first
    entry["nights"] = int(re.sub(r"[^\d]", "", str(nights)) or "1")
    if photo_rel:
        entry["photo"] = photo_rel
    for i, v in enumerate(visits):
        if v.get("id") == hotel["id"] or v.get("name") == hotel["name"]:
            if not photo_rel and v.get("photo"):
                entry["photo"] = v["photo"]     # 既存写真を保持
            visits[i] = entry
            break
    else:
        visits.append(entry)
    return ("ok", hotel["name"])


def main():
    body = os.environ.get("ISSUE_BODY", "")
    if not body:
        print("::error::ISSUE_BODY が空です")
        return 1
    f = parse_issue(body)

    master = load_json(MASTER, {"hotels": []})
    hotels = master.get("hotels", [])
    visits_doc = load_json(VISITS, {"meta": {}, "visits": []})
    visits = visits_doc.setdefault("visits", [])

    # 削除モード（削除フォーム：1行1件の店舗名）
    delete_field = f.get("削除する店舗", "").strip()
    if delete_field:
        removed, notfound = [], []
        for line in delete_field.splitlines():
            name = strip_image_md(line).strip()
            if not name:
                continue
            hotel = match_hotel(name, hotels)
            kid = hotel["id"] if hotel else None
            kname = hotel["name"] if hotel else name
            idx = None
            for i, v in enumerate(visits):
                if (kid and v.get("id") == kid) or norm(v.get("name")) == norm(kname):
                    idx = i
                    break
            if idx is None:
                notfound.append(name)
                continue
            v = visits.pop(idx)
            if v.get("photo"):
                try:
                    os.remove(os.path.join(ROOT, v["photo"]))
                except OSError:
                    pass
            removed.append(v.get("name"))
        json.dump(visits_doc, open(VISITS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if not removed:
            print("STATUS=unmatched")
            print("MESSAGE=削除対象が見つかりませんでした：%s" % "、".join(notfound))
            return 0
        msg = "%d件を削除しました（%s）" % (len(removed), "、".join(removed))
        if notfound:
            msg += " ／ 見つからず：%s" % "、".join(notfound)
        print("STATUS=ok")
        print("MESSAGE=" + msg)
        return 0

    # まとめ投稿（複数行）と 単票（ドロップダウン）の両対応
    records = []
    bulk = f.get("宿泊記録", "").strip()
    if bulk:
        for line in bulk.splitlines():
            line = line.strip()
            if not line:
                continue
            img = extract_image_url(line)
            parts = [p.strip() for p in strip_image_md(line).split("/")]
            if not parts or not parts[0]:
                continue
            records.append((parts[0], parts[1] if len(parts) > 1 else "",
                            parts[2] if len(parts) > 2 else "1", img))
    else:
        records.append((f.get("店舗名", ""), f.get("初宿泊日", "").strip(),
                        f.get("延べ泊数", "") or "1", extract_image_url(f.get("写真", ""))))

    ok, bad = [], []
    for name, first, nights, img in records:
        status, ret = process_record(name, first, nights, img, hotels, visits)
        (ok if status == "ok" else bad).append(ret)

    if not ok and bad:
        print("STATUS=unmatched")
        print("MESSAGE=突合できませんでした：%s（表記を確認してください）" % "、".join(bad))
        return 0

    json.dump(visits_doc, open(VISITS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    msg = "%d件を記録しました（%s）" % (len(ok), "、".join(ok))
    if bad:
        msg += " ／ 突合できず：%s" % "、".join(bad)
    print("STATUS=ok")
    print("MESSAGE=" + msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
