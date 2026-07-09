#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Issue から名所制覇の手動補正を読み取り、data/spot_overrides.json を更新する。

対応する入力は2通り:
  (A) 本文に JSON ブロック（管理ページ spots-admin.html の「Issueで反映」/「コピー」が生成）
      ```json
      { "unvisited": ["sanmeisen_gero"], "visited": [] }
      ```
  (B) Issueフォーム（.github/ISSUE_TEMPLATE/spot-override.yml）のプルダウン選択
      ### 訪問扱いを外す（未訪問にする）
      下呂温泉（岐阜県）／日本三名泉, 有馬温泉（兵庫県）／日本三古湯
      ### 訪問済みにする（任意）
      _No response_

出力は build_dormy_visit.py と同じ規約（STATUS=... / MESSAGE=...）。
"""
import os
import re
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
VISITS = os.path.join(DATA, "spot_visits.json")
OVERRIDES = os.path.join(DATA, "spot_overrides.json")

# フォームの見出し（テンプレートの label と一致させること）
H_UNVISIT = "訪問扱いを外す（未訪問にする）"
H_VISIT = "訪問済みにする（任意）"

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


def build_maps():
    """label -> id と 有効id集合を作る。label は 'name（pref）／category'。"""
    d = load_json(VISITS, {})
    label2id, ids = {}, set()
    for c in d.get("categories", []):
        cname = c.get("name", "")
        for s in c.get("spots", []):
            sid = s.get("id")
            if not sid:
                continue
            ids.add(sid)
            label = "%s（%s）／%s" % (s.get("name", ""), s.get("pref", ""), cname)
            label2id[label] = sid
    return label2id, ids


def extract_json(body):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", body or "", re.S | re.I)
    chunk = m.group(1) if m else None
    if chunk is None:
        m = re.search(r"(\{[^{}]*\"(?:unvisited|visited)\"[^{}]*\})", body or "", re.S)
        chunk = m.group(1) if m else None
    if chunk is None:
        return None
    try:
        obj = json.loads(chunk)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def section(body, heading):
    """Issueフォーム本文から '### heading' 直後のブロックを取り出す。"""
    if not body:
        return ""
    # 見出しから次の見出し(### )または末尾まで
    pat = re.compile(r"^###\s*" + re.escape(heading) + r"\s*$(.*?)(?=^###\s|\Z)", re.S | re.M)
    m = pat.search(body)
    if not m:
        return ""
    return m.group(1).strip()


def parse_selection(block, label2id):
    if not block or block.strip() in ("_No response_", "_なし_", "なし"):
        return [], []
    # カンマ・読点・改行で分割
    parts = re.split(r"[,\n、]+", block)
    ids, unknown = [], []
    seen = set()
    for p in parts:
        p = p.strip().strip("-").strip()
        if not p:
            continue
        sid = label2id.get(p)
        if sid:
            if sid not in seen:
                seen.add(sid)
                ids.append(sid)
        else:
            unknown.append(p)
    return ids, unknown


def as_id_list(v, ids):
    if not isinstance(v, list):
        return [], []
    keep, unknown, seen = [], [], set()
    for x in v:
        if isinstance(x, str):
            x = x.strip()
            if not x:
                continue
            if x in ids:
                if x not in seen:
                    seen.add(x)
                    keep.append(x)
            else:
                unknown.append(x)
    return keep, unknown


def main():
    body = os.environ.get("ISSUE_BODY", "")
    label2id, ids = build_maps()

    unvisited, visited, unknown = [], [], []

    payload = extract_json(body)
    if payload is not None and ("unvisited" in payload or "visited" in payload):
        # (A) 管理ページのJSON
        uv, u1 = as_id_list(payload.get("unvisited"), ids)
        vi, u2 = as_id_list(payload.get("visited"), ids)
        unvisited, visited, unknown = uv, vi, (u1 + u2)
    else:
        # (B) フォームのプルダウン
        uv, u1 = parse_selection(section(body, H_UNVISIT), label2id)
        vi, u2 = parse_selection(section(body, H_VISIT), label2id)
        unvisited, visited, unknown = uv, vi, (u1 + u2)
        if not uv and not vi and not (u1 or u2):
            out("error", "補正内容を読み取れませんでした。管理ページのボタンか、フォームのプルダウンで選択してください。")
            return 0

    # unvisited 優先（両方に入ったIDは未訪問化）
    uvset = set(unvisited)
    visited = [i for i in visited if i not in uvset]

    prev = load_json(OVERRIDES, {})
    doc = {
        "_note": prev.get("_note") or DEFAULT_NOTE,
        "_howto": prev.get("_howto") or DEFAULT_HOWTO,
        "unvisited": sorted(set(unvisited)),
        "visited": sorted(set(visited)),
    }
    with open(OVERRIDES, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    msg = "手動補正を保存しました（未訪問化 %d件 / 訪問化 %d件）。" % (len(doc["unvisited"]), len(doc["visited"]))
    if unknown:
        msg += " 対応づけできず無視：%s" % "、".join(unknown[:6])
    out("ok", msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
