#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""名所制覇まわりの共通処理（ラベル表記と状態計算を一元化）。

ラベル表記はフォーム生成(build_spot_form.py)とIssue解析(apply_spot_override.py)で
完全に一致させる必要があるため、ここに集約する。
"""
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
VISITS = os.path.join(DATA, "spot_visits.json")
OVERRIDES = os.path.join(DATA, "spot_overrides.json")

DEFAULT_NOTE = ("名所制覇の自動判定(proximity)を手動で補正するファイル。"
                "spot_visits.json をGPS履歴から再生成しても、このファイルは上書きされないため補正が残ります。")
DEFAULT_HOWTO = ("Issue『名所制覇の修正』でチェックを付けて送信すると自動更新されます。"
                 "unvisited=訪問扱いを外すID / visited=訪問済みへ強制するID。id は spot_visits.json の spots[].id。")


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def spot_label(cat_name, s):
    """一意ラベル：『名前（県）／カテゴリ』。同名スポットもカテゴリで区別。"""
    return "%s（%s）／%s" % (s.get("name", ""), s.get("pref", ""), cat_name)


def load_state():
    """現在状態を返す。

    戻り値 dict:
      order      : [(id, label, cat_name, spot)]  … 表示順
      auto       : {id: bool}   自動判定（firstVisit有無）
      cur        : {id: bool}   実効状態（override適用後）
      label2id   : {label: id}
      id2label   : {id: label}
      override   : 既存 overrides doc
    """
    d = load_json(VISITS, {})
    ov = load_json(OVERRIDES, {})
    off = set(ov.get("unvisited", []) or [])
    on = set(ov.get("visited", []) or [])

    order, auto, cur, label2id, id2label = [], {}, {}, {}, {}
    for c in d.get("categories", []):
        cname = c.get("name", "")
        for s in c.get("spots", []):
            sid = s.get("id")
            if not sid:
                continue
            label = spot_label(cname, s)
            a = bool(s.get("firstVisit"))
            auto[sid] = a
            cur[sid] = False if sid in off else (True if sid in on else a)
            label2id[label] = sid
            id2label[sid] = label
            order.append((sid, label, cname, s))
    return {
        "order": order, "auto": auto, "cur": cur,
        "label2id": label2id, "id2label": id2label, "override": ov,
    }


def override_from_effective(auto, eff):
    """auto と 望む実効状態 eff から、絶対的な override(unvisited/visited) を導出。"""
    unvisited, visited = [], []
    for sid, a in auto.items():
        e = eff.get(sid, a)
        if a and not e:
            unvisited.append(sid)
        elif (not a) and e:
            visited.append(sid)
    return sorted(set(unvisited)), sorted(set(visited))


def write_override(unvisited, visited):
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
    return doc
