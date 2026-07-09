# 引き継ぎメモ（新チャット再開用）

このファイルは「-志遊- shiyu's station」の現状サマリー。詳細は PROJECT.md 参照。

## 運用の大前提
- 完全静的サイト（GitHub Pages）。**Pages配信は「Deploy from a branch」方式**（GitHub内部が自動デプロイ）。
  Actions方式用の deploy-pages.yml は不採用（入れると赤失敗するので置かない）。
- **ワークフロー系ファイルは push スコープ問題があるため GitHub Web画面から追加/編集**する。
  Actions権限は Settings→Actions→General→Workflow permissions = **Read and write**。
- zip全体を上げると Action 生成物がシードに戻る → 該当 Action を再runで実データに戻る（自己回復）。

## セクション別の現状（旅の記録 = kiroku.html）
- **鉄道乗りつぶし**：`data/rail.json`（`scripts/build_rail.py` が生成）。JR=会社別／私鉄=乗車ある事業者の会社別バー、会社クリックで路線内訳。
  更新＝乗りつぶしオンラインのJR/私鉄画面を全選択コピー→ `data/rail_jr_raw.txt` `data/rail_pr_raw.txt` 差し替え→push→ build-rail.yml が自動再生成。
- **市区町村踏破**：`data/visited_cities.json`（別ツール生成JSONを差し替え）。3〜4列、都道府県クリックで訪問市区町村（政令市は市+区）。
- **名所制覇**：`data/spot_visits.json`（別ツール生成）。三名泉・三景ほか、訪問チップ。
- **ドーミーイン踏破**：下記の二層＋Issue運用。
- レイアウトは全セクション横幅いっぱい可変（.inner=最大1760px）に統一済み。

## ドーミーイン（今回の主実装）
- 二層：`data/dormy_master.json`（全店マスター=分母＆未訪問）＋ `data/dormy_visits.json`（訪問）。
- マスター生成 `scripts/build_dormy_master.py`：Wikipedia（MediaWiki API 生wikitext）を「ドーミーイン」=dormy型／「共立リゾート」=resort型で解析。
  店名からブランド推定（nono/premium/express/resort/dormy）、都道府県→地方、閉館・見出し除外。
  `data/dormy_wiki_raw.txt` があれば貼付け優先。`meta.totalPin` で分母固定可。
  実行時に **Issueフォームのドロップダウン＆コピペ一覧もマスターから自動再生成**する。
  現状は 110店の初期シード（Wikipediaから把握分）。build-dormy-master.yml（月1＋手動）。
  ※共立リゾートは記事が簡略な部分あり。初回実行後に件数確認、不足は raw 貼付けで補完。
- 訪問処理 `scripts/build_dormy_visit.py`：Issue本文を解析。店舗名→マスター突合（表記ゆれ吸収）。
  写真は長辺800pxリサイズ＋**WebP変換** `images/dormy/<id>.webp`。**同じ店の再登録で上書き更新**（写真なし再登録は既存写真保持）。**削除対応**（写真も消す）。
- Issueフォーム4系統（すべて label: dormy-visit → workflow `dormy-visit-action.yml` が処理）：
  - `ISSUE_TEMPLATE/dormy-visit-bulk.yml`（まとめ追加・1行1件＋各行に写真1枚・コピペ一覧つき）
  - `ISSUE_TEMPLATE/dormy-visit.yml`（1件追加・店舗ドロップダウン）
  - `ISSUE_TEMPLATE/dormy-visit-delete.yml`（削除）
- 描画：全体踏破率ヘッドライン＋3ブランド（ドーミーイン{dormy/premium/express}／御宿野乃／共立リゾート）アコーディオン（初期全畳み、見出しに訪問/総数）。展開で訪問カード（写真・温泉名・サブブランドタグ・初宿泊日・延べ泊数）を地方順に上、未訪問（名前＋所在）を淡く下。visits空でも0%表示。

## 既知の宿題・注意
- リポジトリ側で旧 `.github/workflows/dormy-visit.yml`（中身が入れ違った不正ファイル）が残っていれば削除。正は `dormy-visit-action.yml`。
- bot コミットは `[skip build]`（スキップ無効トークン＝branch方式で確実にデプロイ）。
- 残タスク：ブログ初回記事（blog.json）、プロフィール以外の細部、共立リゾート件数の実確認。

## 動作検証状況（このzip時点）
- kiroku.html：全セクション jsdom で描画確認済み。ドーミーインは追加/まとめ/削除/上書き/表記ゆれを単体テスト済み。
- build_dormy_master.py：二モード解析・ブランド分類・Issueテンプレ生成をサンプルで検証。ただし **Wikipedia API 実取得は本番の初回runで要確認**（サンドボックス不可のため）。
- 画像 WebP 保存を実地確認。
