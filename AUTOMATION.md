# 自動更新のしくみ（最新動画・お知らせ）

このサイトは **GitHub Actions＋Python** で、最新動画とお知らせを自動更新します。
サーバーは不要で、GitHub Pages のまま運用できます。

## 何が自動で更新されるか
1. **最新動画（`#latest` カルーセル）**
   両チャンネルのRSSから新しい順に取得し、`index.html` の `AUTO:LATEST` 区間を丸ごと書き換えます。
2. **代表動画のタイトル（`#rail` / `#taiko`）**
   `data/videos.json` に登録した動画のタイトルを oEmbed で取得し、カードの見出しを更新します。
   （リンクは `videos.json` の登録内容、サムネイルとタイトルはYouTubeから自動取得します）
3. **お知らせ（`#news`）**
   新しい動画を検知すると、定型文で `AUTO:NEWS` 区間に追記します（最大 `news_max` 件）。
   ブログを更新した場合も、`data/blog.json` に追記すれば同様にお知らせへ反映されます。

## 実行タイミング
- 6時間ごとに自動実行（`.github/workflows/update-videos.yml` の `cron`）
- 手動実行も可：リポジトリの **Actions → Update videos & news → Run workflow**

## 初回セットアップ
1. リポジトリの **Settings → Actions → General → Workflow permissions** を
   **「Read and write permissions」** に設定（自動コミットに必要）。
2. **Settings → Pages** で公開元ブランチを指定（例：`main` / `root`）。
3. Actions タブから一度 **Run workflow** を実行。
   - 初回は既存動画をお知らせに大量表示しないよう、**IDのシードのみ**行います
     （＝この時点では「新着動画」お知らせは追加されません）。
   - 代表動画タイトルと最新動画カルーセルはこの初回実行で反映されます。
4. 以降、新しい動画を投稿すると次回の実行で自動的に「新着動画」お知らせが付きます。

## 設定ファイル
### `data/videos.json`
- `channels.rail / taiko`：`handle`（@付き）、表示名 `name`、バッジ `badge`。
  ハンドルからチャンネルIDは自動解決します。固定したい場合は `channel_id` に `UC...` を記入。
- `representative.rail / taiko`：代表動画の `url`（サムネイルはYouTubeから自動取得。`thumb` は未使用）。
- `latest_count`：カルーセルに載せる最新動画の最大数。
- `news_max`：お知らせの保持件数。
- `news_templates`：`{channel}` `{title}` を差し込む定型文。

### `data/blog.json`（ブログ更新のお知らせ用）
記事を公開したら `posts` の先頭に追記します。
```json
{ "posts": [
  { "id": "2026-07-05-only-line", "title": "只見線で秋を追う", "url": "blog.html#only-line", "date": "2026-07-05" }
] }
```
`id` が未通知のものを検知すると、次回実行で「ブログを更新しました：〈タイトル〉」を追加します。

### `data/last_seen.json`
スクリプトが管理する状態ファイル（既知ID・お知らせ履歴）。**手動編集しないでください。**

## 手動で動かす場合（ローカル確認）
```bash
python scripts/update_videos.py
```
標準ライブラリのみで動作します（追加インストール不要）。

## マーカーについて
`index.html` の以下の区間だけをスクリプトが書き換えます。**マーカーの外**は手動編集して構いません。
```
<!-- AUTO:LATEST:START --> … <!-- AUTO:LATEST:END -->
<!-- AUTO:RAIL:START -->   … <!-- AUTO:RAIL:END -->
<!-- AUTO:TAIKO:START -->  … <!-- AUTO:TAIKO:END -->
<!-- AUTO:NEWS:START -->   … <!-- AUTO:NEWS:END -->
```
（お知らせの手動項目は `AUTO:NEWS:END` の外側に置けば消えません。）
