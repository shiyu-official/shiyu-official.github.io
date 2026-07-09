# -志遊- shiyu's station ｜ サイト一式

GitHub Pages にそのまま置ける静的サイトです。
リポジトリ直下（`index.html` がルートに来る形）に展開してください。

## 構成
```
index.html            トップ（全セクション・実リンク反映済み）
contact.html          お問い合わせ（Googleフォーム連携・非同期送信）
blog.html             ブログ（準備中スタブ／記事スケルトンをコメント内蔵）
kiroku.html           旅の記録（乗りつぶし/踏破/ドーミーイン・準備中）
privacy.html          プライバシーポリシー（ひな形・要確認）
css/                  theme / style / inview / contact
js/                   main / jquery.inview_set
images/               画像一式
data/                 videos.json（設定）/ blog.json / last_seen.json（状態）
scripts/update_videos.py        自動更新スクリプト（標準ライブラリのみ）
.github/workflows/update-videos.yml  定期実行ワークフロー
AUTOMATION.md         自動更新の運用手順
```

## 反映済みのリンク
- Re:しゆ（旅行・鉄道）: https://www.youtube.com/@Re_shiyu_travel
- 太鼓の達人: https://www.youtube.com/@Re_shiyu_taiko
- X: https://x.com/shiyu_official_
- 代表動画（旅行4本／太鼓4本）: `data/videos.json` に登録済み
  ※カードのタイトルは自動更新スクリプトが oEmbed で取得します（下記）。

## 自動更新（最新動画・お知らせ）
詳細は **AUTOMATION.md** を参照。要点だけ：
1. Settings → Actions → General → Workflow permissions を **Read and write** に。
2. Settings → Pages で公開ブランチを設定。
3. Actions → **Update videos & news** → **Run workflow** を一度実行。
   - 初回は既存動画を大量通知しないよう **IDのシードのみ**（お知らせは増えません）。
   - このとき最新動画カルーセルと代表動画タイトルが反映されます。
4. 以降は6時間ごとに自動実行。新規投稿は次回実行で「新着動画」お知らせが付きます。
   ブログは `data/blog.json` に追記すると同様にお知らせへ反映されます。

## お問い合わせフォーム
Googleフォームへ隠しiframe経由でPOST（ページ遷移なし）。
entry対応（確認済み）：`1383982872`=お名前 / `94781560`=メール / `1334466102`=内容。

## 動作メモ
- 外部CDN（Google Fonts / Font Awesome / jQuery / jquery.inview）を読み込みます。
- ブレイクポイント：ハンバーガー 900px、フォーム1カラム 767px、ヒーロー縦積み 700px。
- `prefers-reduced-motion` 指定時は演出を無効化します。

## 追加ファイル（本番運用の仕上げ）
- `404.html`：存在しないURL用（GitHub Pagesが自動表示。絶対パス指定でどの階層でも崩れません）
- `robots.txt` / `sitemap.xml`：クローラ向け
- `index.html` 内 JSON-LD（Organization/WebSite）＋ theme-color

## 旅の記録（kiroku）のデータ入力
`data/kiroku.json` に数値を入れると `kiroku.html` に自動反映されます（空欄は「準備中」表示）。
- `lines`: `[{ "name":"JR北海道", "done":1200, "total":2500, "note":"" }]`（done/total で達成率バー）
- `municipalities`: `{ "visited":300, "total":1741, "note":"" }`
- `dormy`: `[{ "name":"ドーミーイン◯◯", "date":"2026-06-01", "note":"" }]`
