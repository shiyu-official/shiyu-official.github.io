#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Issue『名所制覇の修正』を解析し、data/spot_overrides.json を更新する。

フォームは現在状態つきのチェックボックス2群（build_spot_form.py が生成）:
  ### 現在【訪問済み ✓】…
  - [x] 下呂温泉（岐阜県）／日本三名泉
  ### 現在【未訪問 ・】…
  - [ ] 道後温泉（愛媛県）／日本三古湯

解析方針: 「チェックされた項目＝その状態を反転」。項目が今どちらかは
data から計算するので、どちらの群にあったかを気にせず反転できる。
互換: 本文に JSON ブロックがあればそれを優先（旧・管理ページ経由）。

出力は build_dormy_visit.py と同じ規約（STATUS=... / MESSAGE=...）。
"""
import os
import re
import sys
import json
import spot_common as sc


def out(status, message):
    print("STATUS=" + status)
    print("MESSAGE=" + message)


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


def checked_labels(body):
    """本文中の `- [x] ラベル` を全部拾う（大文字X/前後空白許容）。"""
    res = []
    for m in re.finditer(r"^[ \t>*-]*\[[xX]\]\s+(.+?)\s*$", body or "", re.M):
        res.append(m.group(1).strip())
    return res


def main():
    body = os.environ.get("ISSUE_BODY", "")
    st = sc.load_state()
    auto, cur = st["auto"], st["cur"]
    label2id, ids = st["label2id"], set(st["auto"].keys())

    unknown = []

    payload = extract_json(body)
    if payload is not None and ("unvisited" in payload or "visited" in payload):
        # 互換：JSONが来たら絶対値としてそのまま採用
        def clean(v):
            keep = []
            for x in (v or []):
                if isinstance(x, str) and x.strip() in ids:
                    keep.append(x.strip())
                elif isinstance(x, str) and x.strip():
                    unknown.append(x.strip())
            return keep
        unvisited = clean(payload.get("unvisited"))
        visited = clean(payload.get("visited"))
        # 両方に入ったら unvisited 優先
        visited = [i for i in visited if i not in set(unvisited)]
        doc = sc.write_override(unvisited, visited)
    else:
        # チェックボックス：チェックされたものを反転
        labels = checked_labels(body)
        flip_ids = []
        for lb in labels:
            sid = label2id.get(lb)
            if sid:
                flip_ids.append(sid)
            else:
                unknown.append(lb)
        if not flip_ids and not unknown:
            out("ok", "変更はありませんでした（チェックなし）。")
            return 0

        eff = dict(cur)
        for sid in flip_ids:
            eff[sid] = not cur[sid]
        unvisited, visited = sc.override_from_effective(auto, eff)
        doc = sc.write_override(unvisited, visited)

    msg = "修正を保存しました（未訪問化 %d件 / 訪問化 %d件）。" % (len(doc["unvisited"]), len(doc["visited"]))
    if unknown:
        msg += " 対応づけできず無視：%s" % "、".join(unknown[:6])
    out("ok", msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
