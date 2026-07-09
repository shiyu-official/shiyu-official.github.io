#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Issueフォーム/本文の JSON を読み取り、data/spot_overrides.json を更新する。

本文には次のような JSON ブロックが含まれる想定（spots-admin.html が生成）:

    ```json
    { "unvisited": ["sanmeisen_gero"], "visited": [] }
    ```

出力は build_dormy_visit.py と同じ規約（STATUS=... / MESSAGE=...）。
ワークフローがこれを拾ってIssueにコメントしクローズするのはDormyと同様。
"""
import os
import re
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
VISITS = os.path.join(DATA, "spot_visits.json")
OVERRIDES = os.path.join(DATA, "spot_overrides.json")

DEFAULT_NOTE = ("名所制覇の自動判定(proximity)を手動で補正するファイル。"
                "spot_visits.json をGPS履歴から再生成しても、このファイルは上書きされないため補正が残ります。")
DEFAULT_HOWTO = ("近くを通っただけ等で誤って訪問扱いになったスポットの id を unvisited に追加。"
                 "逆に自動検出されなかったが訪問済みにしたい場合は visited に追加。id は data/spot_visits.json の spots[].id。")


def out(status, message):
    print("STATUS=" + status)
    print("MESSAGE=" + message)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def valid_ids():
    d = load_json(VISITS, {})
    ids = set()
    for c in d.get("categories", []):
        for s in c.get("spots", []):
            if s.get("id"):
                ids.add(s["id"])
    return ids


def extract_json(body):
    """本文から JSON オブジェクトを取り出す。優先: ```json ... ``` フェンス、次に最初の {...}。"""
    if not body:
        return None
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", body, re.S | re.I)
    if m:
        chunk = m.group(1)
    else:
        m = re.search(r"(\{.*\})", body, re.S)
        if not m:
            return None
        chunk = m.group(1)
    try:
        return json.loads(chunk)
    except Exception:
        return None


def as_id_list(v):
    if not isinstance(v, list):
        return []
    seen, res = set(), []
    for x in v:
        if isinstance(x, str):
            x = x.strip()
            if x and x not in seen:
                seen.add(x)
                res.append(x)
    return res


def main():
    body = os.environ.get("ISSUE_BODY", "")
    payload = extract_json(body)
    if payload is None:
        out("error", "本文からJSONを読み取れませんでした。管理ページの『Issueで反映』から作成してください。")
        return 0

    unvisited = as_id_list(payload.get("unvisited"))
    visited = as_id_list(payload.get("visited"))

    ids = valid_ids()
    unknown = [i for i in (unvisited + visited) if i not in ids]
    unvisited = [i for i in unvisited if i in ids]
    visited = [i for i in visited if i in ids]

    # 同一IDが両方に入っていたら unvisited を優先（＝未訪問化）
    vset = set(visited)
    both = [i for i in unvisited if i in vset]
    if both:
        visited = [i for i in visited if i not in set(unvisited)]

    prev = load_json(OVERRIDES, {})
    doc = {
        "_note": prev.get("_note") or DEFAULT_NOTE,
        "_howto": prev.get("_howto") or DEFAULT_HOWTO,
        "unvisited": sorted(unvisited),
        "visited": sorted(visited),
    }
    with open(OVERRIDES, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    msg = "手動補正を保存しました（未訪問化 %d件 / 訪問化 %d件）。" % (len(unvisited), len(visited))
    if unknown:
        msg += " 未知のIDは無視：%s" % "、".join(unknown[:8])
    out("ok", msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
