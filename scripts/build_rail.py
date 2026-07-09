#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
乗りつぶしオンラインの画面コピーから data/rail.json を生成する。

入力（utf-8 / cp932 いずれも可・どちらか/両方が存在すればよい）:
  data/rail_jr_raw.txt … JRのページを全選択コピーしたテキスト
  data/rail_pr_raw.txt … 私鉄等のページを全選択コピーしたテキスト

生成物 rail.json:
  jr      : { total, companies:[{name,eigyo,jousha,mijou,rate, lines:[{name,eigyo,jousha,rate}]}] }
  private : { total, divisions:[{区分}], companies:[{name,division,...,lines:[...]}] }

サマリー表（会社名/区分 × 営業km/乗車km/未乗km/乗車率）と、
路線ごとの明細（会社→路線の営業km/乗車km）を抽出する。明細のゴミ
（タブ折返し・edit/delete・post_add・chat_bubble 等）は除去する。

更新方法: 上記2ファイルにページ全体を貼り替えてコミットするだけ。
"""
import json, os, re, sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

HEADER_TAIL = ["営業km", "乗車km", "未乗km", "乗車率"]
DIVISIONS = ["大手私鉄", "準大手私鉄", "公営企業", "私鉄一般",
             "モノレール", "新交通システム", "ケーブルカー等専業", "浮上式"]
UI = {"post_add", "chat_bubble", "edit", "delete", "編集", "乗車区間", "区間km",
      "乗車日", "未乗", "路線名", "起点", "終点", "営業km", "乗車km", "未乗km",
      "会社名", "区分"}


def read_text(path):
    if not os.path.exists(path):
        return ""
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def clean_lines(text):
    return [ln.strip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if ln.strip()]


def toks(line):
    return [t for t in re.split(r"[\t 　]+", line.strip()) if t]


def is_dec(s):
    return bool(re.fullmatch(r"\d+(?:\.\d+)?", s))


def is_date(s):
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", s))


def to_float(s):
    try:
        return float(str(s).replace(",", ""))
    except ValueError:
        return None


def parse_rate(s):
    m = re.match(r"^\s*([-\d.]+)\s*%?\s*$", str(s))
    return to_float(m.group(1)) if m else None


def extract_table(lines, key_label, stop_labels=None):
    """key_label('会社名'/'区分') の 5行1レコード サマリー表を1つ抽出。"""
    stop_labels = stop_labels or []
    n = len(lines)
    i = 0
    while i < n:
        if lines[i] == key_label and i + 4 < n and lines[i + 1:i + 5] == HEADER_TAIL:
            j = i + 5
            recs = []
            while j + 4 < n:
                name = lines[j]
                if name.startswith("順位") or name in stop_labels:
                    break
                e, ju, mi, ra = (to_float(lines[j + 1]), to_float(lines[j + 2]),
                                 to_float(lines[j + 3]), parse_rate(lines[j + 4]))
                if None in (e, ju, mi, ra):
                    break
                recs.append({"name": name, "eigyo": round(e, 1), "jousha": round(ju, 1),
                             "mijou": round(mi, 1), "rate": round(ra, 3)})
                j += 5
            return recs
        i += 1
    return []


def extract_operators(lines):
    """『事業者ごとの状況』の会社別表（区分見出しでグループ）を抽出。"""
    ops = []
    n = len(lines)
    try:
        start = lines.index("事業者ごとの状況")
    except ValueError:
        return ops
    div = None
    i = start + 1
    while i < n:
        ln = lines[i]
        if ln == "路線ごとの状況":
            break
        if ln in DIVISIONS:
            div = ln
            i += 1
            continue
        if ln == "会社名" and i + 4 < n and lines[i + 1:i + 5] == HEADER_TAIL:
            j = i + 5
            while j + 4 < n:
                name = lines[j]
                if name.startswith("順位") or name in DIVISIONS or name == "路線ごとの状況":
                    break
                e, ju, mi, ra = (to_float(lines[j + 1]), to_float(lines[j + 2]),
                                 to_float(lines[j + 3]), parse_rate(lines[j + 4]))
                if None in (e, ju, mi, ra):
                    break
                ops.append({"name": name, "division": div, "eigyo": round(e, 1),
                            "jousha": round(ju, 1), "mijou": round(mi, 1), "rate": round(ra, 3)})
                j += 5
            i = j
            continue
        i += 1
    return ops


def parse_line_detail(text):
    """会社→路線[{name,eigyo,jousha,rate}] を抽出（明細のゴミは除去）。"""
    result = {}
    company = None
    frag = []
    prev = ""
    for raw in text.replace("\r", "").split("\n"):
        s = raw.strip()
        if not s:
            prev = s
            continue
        tk = toks(s)
        if tk and tk[0] == "路線名" and "起点" in tk:  # 明細ヘッダ → 直前が会社名
            company = prev
            result.setdefault(company, [])
            frag = []
            prev = s
            continue
        if any(is_date(t) for t in tk):  # 区間行
            frag = []
            prev = s
            continue
        core = [t for t in tk if t not in UI]
        if len(core) >= 5 and is_dec(core[-1]) and is_dec(core[-2]) and is_dec(core[-3]):
            e, ju, mi = float(core[-3]), float(core[-2]), float(core[-1])
            if abs(ju + mi - e) < 0.2:
                name = ("".join(frag) + "".join(core[:-5])).strip()
                if company is not None:
                    result[company].append({"name": name or "(名称不明)",
                                            "eigyo": round(e, 1), "jousha": round(ju, 1),
                                            "rate": round(ju / e * 100, 1) if e else 0.0})
                frag = []
                prev = s
                continue
        if all(t in UI for t in tk):
            frag = []
            prev = s
            continue
        if len(tk) == 1:
            frag.append(tk[0])
        prev = s
    return result


def split_total(records, total_name):
    total, rows = None, []
    for r in records:
        if r["name"] == total_name:
            total = r
        else:
            rows.append(r)
    if total is None and rows:
        te = round(sum(r["eigyo"] for r in rows), 1)
        tj = round(sum(r["jousha"] for r in rows), 1)
        total = {"name": total_name, "eigyo": te, "jousha": tj,
                 "mijou": round(te - tj, 1), "rate": round(tj / te * 100, 3) if te else 0.0}
    return total, rows


def attach_lines(companies, detail):
    for c in companies:
        if c["name"] in detail:
            c["lines"] = detail[c["name"]]


def main():
    jr_text = read_text(os.path.join(DATA, "rail_jr_raw.txt"))
    pr_text = read_text(os.path.join(DATA, "rail_pr_raw.txt"))
    combined_lines = clean_lines(jr_text + "\n" + pr_text)

    jr_total, jr_companies = split_total(extract_table(combined_lines, "会社名", DIVISIONS), "JR全線")
    pr_total, pr_divisions = split_total(extract_table(combined_lines, "区分"), "私鉄全線")
    pr_companies = extract_operators(combined_lines)

    detail = {}
    detail.update(parse_line_detail(jr_text))
    detail.update(parse_line_detail(pr_text))
    attach_lines(jr_companies, detail)
    attach_lines(pr_companies, detail)

    if not jr_companies and not pr_divisions:
        sys.stderr.write("[build_rail] サマリー表が見つかりませんでした。raw txt を確認してください。\n")

    jst = timezone(timedelta(hours=9))
    out = {
        "meta": {"generated": datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S%z")},
        "jr": {"total": jr_total, "companies": jr_companies} if jr_companies else None,
        "private": {"total": pr_total, "divisions": pr_divisions,
                    "companies": pr_companies} if pr_divisions else None,
    }
    with open(os.path.join(DATA, "rail.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("[build_rail] wrote data/rail.json")
    if jr_companies:
        wl = sum(1 for c in jr_companies if c.get("lines"))
        print(f"  JR: {len(jr_companies)}社（路線内訳あり {wl}社）/ 全線 {jr_total['rate']}%")
    if pr_divisions:
        print(f"  私鉄: {len(pr_divisions)}区分 / {len(pr_companies)}社 / 全線 {pr_total['rate']}%")


if __name__ == "__main__":
    main()
