#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""現在の訪問状態から、チェックボックス式のIssueフォームを生成する。

出力: .github/ISSUE_TEMPLATE/spot-override.yml
- 現在【訪問済み】のスポット群と【未訪問】のスポット群に分け、
  「間違っているものにチェック＝反転」で直せるようにする。
- spot_visits.json / spot_overrides.json が変わるたびに再生成して最新状態を保つ。
"""
import os
import datetime
import spot_common as sc

TEMPLATE = os.path.join(sc.ROOT, ".github", "ISSUE_TEMPLATE", "spot-override.yml")

H_VISITED = "現在【訪問済み ✓】… 実は通過しただけ＝未訪問に直すものにチェック"
H_UNVISITED = "現在【未訪問 ・】… 実は訪問済み＝訪問済みに直すものにチェック"


def yq(s):
    """YAMLの二重引用符文字列としてエスケープ。"""
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def checkbox_field(field_id, label, labels):
    if not labels:
        # チェックボックスは最低1項目必要。該当なしは説明文で代替。
        return (
            "  - type: markdown\n"
            "    attributes:\n"
            "      value: |\n"
            "        **" + label + "**\n"
            "        （該当なし）\n"
        )
    lines = [
        "  - type: checkboxes",
        "    id: " + field_id,
        "    attributes:",
        "      label: " + yq(label),
        "      options:",
    ]
    for lb in labels:
        lines.append("        - label: " + yq(lb))
    return "\n".join(lines) + "\n"


def main():
    st = sc.load_state()
    visited_labels, unvisited_labels = [], []
    for sid, label, cname, s in st["order"]:
        if st["cur"][sid]:
            visited_labels.append(label)
        else:
            unvisited_labels.append(label)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    nvis, nall = len(visited_labels), len(st["order"])

    head = (
        "name: 名所制覇の修正\n"
        "description: 訪問/未訪問の誤りを、チェックを付けて直します（現在の状態つき・自動生成）\n"
        'title: "[spots] 名所制覇の修正"\n'
        'labels: ["spot-override"]\n'
        "body:\n"
        "  - type: markdown\n"
        "    attributes:\n"
        "      value: |\n"
        "        現在の判定を一覧にしています（" + now + " 時点 ・ " + str(nvis) + "/" + str(nall) + " 訪問）。\n"
        "        **間違っているものにチェックを入れて送信**してください。チェックした名所だけ状態が反転します（チェックなし＝現状維持）。\n"
    )

    body = (
        head
        + checkbox_field("to_unvisited", H_VISITED, visited_labels)
        + checkbox_field("to_visited", H_UNVISITED, unvisited_labels)
    )

    os.makedirs(os.path.dirname(TEMPLATE), exist_ok=True)
    with open(TEMPLATE, "w", encoding="utf-8") as f:
        f.write(body)
    print("wrote %s (visited=%d, unvisited=%d)" % (TEMPLATE, nvis, nall - nvis))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
