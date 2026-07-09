# -志遊- shiyu's station ｜ プロジェクト仕様・引き継ぎ書

このドキュメントは、別のチャット／別の担当が作業を引き継げるようにするための
**プロジェクト全体の仕様書**です。サイトの構造・デザイン規約・各コンポーネントの
仕組み・編集方法・未確定事項・作業履歴をまとめています。

---

## 0. これは何のサイトか
- 運営者：しゆ（shiyu）
- 内容：YouTube 2チャンネル（旅行・鉄道「Re:しゆ」／太鼓の達人）のハブサイト。
  ブログ・旅の記録も展開予定。
- 実体：**完全静的サイト（HTML/CSS/JS のみ）**。GitHub Pages で公開。
  最新動画とお知らせは GitHub Actions＋Python で自動更新。
- トーン：和風・白基調・藍色＋朱色アクセント・明朝体。
- リポジトリ名は `shiyu-official.github.io`（ユーザーPages。ルート直下に index.html）。

---

## 1. ディレクトリ構成
```
shiyu-official.github.io/
├── index.html            トップ（全セクション）
├── contact.html          お問い合わせ（Googleフォーム連携）
├── blog.html             ブログ（data/blog.json から自動一覧。無ければ準備中）
├── kiroku.html           旅の記録（data/kiroku.json から描画。無ければ準備中）
├── privacy.html          プライバシーポリシー（ひな形・要確認）
├── 404.html              not found（絶対パス指定）
├── css/
│   ├── theme.css         デザイントークン（色・フォント・余白・幅）
│   ├── style.css         構造・レイアウト・レスポンシブ・アニメ（本体）
│   ├── inview.css        スクロールイン演出
│   └── contact.css       お問い合わせフォーム専用
├── js/
│   ├── main.js           メニュー/スクロール/ヒーロー/カルーセル/ページトップ等
│   └── jquery.inview_set.js  スクロールイン（IntersectionObserver・依存なし）
├── data/
│   ├── videos.json       自動更新の設定（チャンネル・代表動画・お知らせ定型文）
│   ├── blog.json         ブログ記事（公開時に追記）
│   ├── kiroku.json       ドーミーイン踏破（dormy）
│   ├── rail.json         鉄道乗りつぶし（build_rail.py が生成）
│   ├── rail_jr_raw.txt   JR画面コピー（貼り替えて更新）
│   ├── rail_pr_raw.txt   私鉄等画面コピー（貼り替えて更新）
│   ├── visited_cities.json  市区町村踏破（別ツール生成JSONを差し替え）
│   ├── spot_visits.json  名所制覇（別ツール生成JSONを差し替え）
│   └── last_seen.json    自動更新の状態（手動編集しない）
├── scripts/update_videos.py   自動更新スクリプト（標準ライブラリのみ）
├── .github/workflows/update-videos.yml  定期実行ワークフロー
├── images/               画像一式（下記）
├── robots.txt / sitemap.xml / .nojekyll
├── AUTOMATION.md         自動更新の運用手順
├── README.md             セットアップ要点
└── PROJECT.md            ← このファイル
```

### 画像アセット（images/）
- hero-1〜3.jpg（+_s は縮小版）：ヒーロースライド
- about-1/2.jpg：ABOUTの写真（blob型マスクで表示）
- category-1〜4.jpg：カテゴリ4枚（旅行/太鼓/記録/ブログ）※横長 1800×600
- contact-bg.jpg：お問い合わせ背景
- logo.png / ogp.png / favicon-32/512.png / apple-touch-icon.png
- kazari1/2/3.webp：装飾（1/2＝ABOUT角、3＝カテゴリ上の波）
- icons/ico-about-1〜3.png、ico-ch-rail/taiko.png：アイコン
- map1.webp：**現在未使用**（ヒーロー刷新で外した。旅の記録等で再利用可）
- video-latest-*/rail-*/taiko-*.jpg：**現在未使用**（サムネはYouTubeから自動取得に変更）

---

## 2. デザイントークン（css/theme.css）
```
--bg-color:#fff  --bg-inverse-color:#020202  --bg-border-color:#ccc
--primary-color:#5c89af（藍）  --primary-dark-color:#3f6a8e
--light-color:#f1f4f8  --light2-color:#f7f5f3
--accent-color:#c93911（朱）  --muted-color:#6a7683
--base-font: Noto Serif JP（明朝）  --accent-font: Cormorant Garamond（英字装飾）
--base-font-size: clamp(13px,0.29vw+11.9px,16px)  --line-height:2
--content-max:1760px（中身の最大幅）
--radius:14px  --shadow-1 / --shadow-2  --ease  --dur:.3s
```
外部CDN：Google Fonts（Noto Serif JP / Cormorant Garamond）、Font Awesome 6.5.2、
jQuery 3.6.0（main.js用。inview_set は非依存）。

### 幅と余白の方針
- コンテナ：`.inner { width: min(94%, var(--content-max)); margin-inline:auto; }`
  → 画面端に寄せつつ、%指定＋`body{overflow-x:hidden}` で**最大化時も横スクロールなし**。
- セクション上下：`.section{ padding-block: clamp(1.6rem,3.2vw,2.8rem) }`、
  `--tight` はさらに狭い。全体的に縦余白は詰めてある。
- ブレイクポイント：ハンバーガー 900px／フォーム1カラム 767px／
  ヒーロー縦積み・カード2列 700px／カテゴリ全幅→カード 900px。

---

## 3. 各セクション（index.html）と対応クラス
上から：ヒーロー → About → 最新動画 → カテゴリ → 旅行・交通 → 太鼓 →
チャンネル/SNS → お知らせ → お問い合わせ → フッター。

### 3.1 ヒーロー `.mainimg`
- 画像を全面に敷き、**左に白の斜めグラデーション**（`.mainimg::before`,
  `linear-gradient(112deg, #fff…→透明)`）を重ね、その白地の上に見出しを左オーバーレイ。
- 3枚クロスフェード＋ケンバーンズ（`main.js initHero`）。`is-active`/`is-zoom`。
- 縦書き帯「記憶と記録のすべてを、今ここで。」を右上に白帯で配置（`.mainimg__tate`）。
- インジケーター（`.mainimg__dots`、#ccc／アクティブ朱色）。
- 見出し：`.mainimg__copy`「志遊の凪音」＋英字サブ「shiyu's station」。
- 700px以下は画像上・テキスト下に縦積み（斜め境界・縦書き帯は非表示）。

### 3.2 About `#about .grid1`
- 3カラム `1.35fr .9fr 1.35fr`（左右に大きな写真、中央に本文＋3アイコン）。
- 写真は blob 型 `mask-image`（`@supports`内）＋角に kazari1/2。
- 見出し `#about .sec-title`「旅する記憶と、紡ぐ記録。」は901px以上で**1行固定**（nowrap）。
- 本文 `.profile`（サンプル。**要差し替え**）、3項目 `.about-cols`（区切り線付き）。

### 3.3 最新動画 `#latest .list1.list-auto`
- 自動取得のカルーセル。`main.js` の `Carousel` が `.track`＋クローンで無限ループ化。
- PC4枚/モバイル2枚、自動送り4s、左右矢印＋スワイプ＋ドット。
- 中身は `AUTO:LATEST` マーカー間をスクリプトが上書き。

### 3.4 カテゴリ `#category .effects-overlay`（重要・調整多め）
- **画面全幅バナー**（`width:100vw; margin-left:calc(50% - 50vw)`）。
- 4枚のタイル `.tile`（各 `<a>`）を **clip-path の平行四辺形で斜めに切り、
  隣と重ねて（margin-left 負）噛み合わせ**て斜め分割。白い帯は使わない。
  - 継ぎ目は画像同士を数px重ねて隙間を殺す（`margin-left: calc(-slant -7px)`）。
    保険で `.effects-overlay{ background:#0e1e2b }`。
  - 斜めの量：`--slant: clamp(34px,4vw,78px)`（浅くすると均等に見える）。
  - 両端の外側は直線（first/last だけ clip 形状を変更）。
- 各タイル：`.tile__inner > .tile__bg(img) + .tile__veil(黒幕) + .tile__cap(見出し)`。
  ホバーで黒幕が退場＋画像ズーム。テキストは正立（skewは使わない＝斜体化しない）。
- 上の波装飾 `.category-deco`（kazari3）は**負の margin-bottom でバナー背面に重ね**、
  間延びを防止。
- 900px以下は通常カード（2列→1列）にフォールバック。
- **別案メモ**（未採用。要望あれば差し替え可）：①細い斜め区切り線、
  ②ホバーで枠が広がるアコーディオン、③縦長パネル4枚。

### 3.5 代表動画 `#rail` / `#taiko`（`.list1`）
- 4枚ずつの枠付きカード（`.card`＝白枠＋影、サムネ＋タイトルを1枠に）。
- リンク・動画IDは実データ（下記）。**サムネ・タイトルはYouTubeから自動取得**。
  - タイトル未取得時は「▶ YouTube で見る」表示。Actions実行で実タイトルに。
- 章末に「チャンネルを見る」ボタン（`.sec-foot`、間隔広め）。

### 3.6 チャンネル/SNS `#links .list3`
- 3枚のカード（Re:しゆ／太鼓／X）。リンクは実URL反映済み。

### 3.7 お知らせ `#news dl.news`
- **セクション幅いっぱい・左揃え**（タイトルと同じ左位置）。
- `AUTO:NEWS` マーカー間を自動追記（最大 news_max 件）。マーカー外は手動項目。

### 3.8 お問い合わせ誘導 `#contact .cta-band .contact-bubble`
- 背景画像＋白い吹き出しボックス（右下だけ角丸なし）。本文＋フォームへのボタン。

### 3.9 フッター／ページトップ／ハンバーガー
- 追従ヘッダー（`header.is-scrolled` でスクロール時に縮小＋影）。
- スキップリンク・フォーカス可視化・`prefers-reduced-motion` 対応済み。

---

## 4. 主要JSの仕組み（js/main.js）
- `applyScreenClass`：900px 境に body へ large-/small-screen。
- メニュー開閉／ドロップダウン（PC hover・タッチ click）／オーバーレイ。
- 自前スムーススクロール（500ms、ハッシュ直リンク対応、追従ヘッダー分オフセット）。
- `initHero`：3枚クロスフェード＋ケンバーンズ、ドット、visibility で一時停止。
- `Carousel`：`.list1.list-auto` を無限ループ化。矢印/スワイプ/ドット、排他制御、
  リサイズ再構築。`prefers-reduced-motion` で自動送り停止。
- ページトップ表示＋ヘッダー影の scroll 連動。
- **inview は依存なしの IntersectionObserver**（`jquery.inview_set.js`）。
  `.inview`＋任意の `data-fx`（up/down/transform1-3/blur、既定up）で
  `is-inview` を付与→ `inview.css` の演出発火。1.2s の保険あり。

---

## 5. 自動更新（詳細は AUTOMATION.md）
- `scripts/update_videos.py`（標準ライブラリのみ）：
  1. 両チャンネルRSSから最新→ `AUTO:LATEST` を再生成
  2. 代表動画の**タイトルとサムネ**を oEmbed / i.ytimg から更新（`AUTO:RAIL/TAIKO`）
  3. 新着動画・新規ブログ記事を検知→ `AUTO:NEWS` に定型文で追記
  4. 状態を `data/last_seen.json` に保存（初回はIDシードのみ＝通知洪水防止）
- `.github/workflows/update-videos.yml`：6時間ごと＋手動。差分あれば自動コミット。
- 設定は `data/videos.json`（channels の handle、representative の url、
  news_templates、latest_count、news_max）。

### 反映済みの実データ
- Re:しゆ（旅行）: https://www.youtube.com/@Re_shiyu_travel
- 太鼓の達人: https://www.youtube.com/@Re_shiyu_taiko
- X: https://x.com/shiyu_official_
- 代表動画（旅行）: S-G6yt2by_k / CCLNgN8DZBo / aDjC0D9wY7g / OcRuTaagVp4
- 代表動画（太鼓）: Rfz7GcOEqMg / odBJofnCiE4 / XS4FjI2lwkw / hHwiDI4ynxg
- Googleフォーム entry：1383982872=お名前 / 94781560=メール / 1334466102=内容（確認済み）

---

## 6. 編集ガイド（よくある変更）
- 色・フォント・幅を変える → `css/theme.css` のトークン。
- セクションの上下余白 → `.section` / `.section--tight` の padding-block。
- コンテンツ幅（画面端への寄せ）→ `.inner` の `min(94%, --content-max)`。
- カテゴリの斜め具合 → `.effects-overlay` の `--slant`。継ぎ目が気になる時は
  タイルの `margin-left` の重なり量（-7px）を増減。全幅をやめる時は
  `width/margin-left` の 100vw 指定を外す。
- 代表動画を差し替え → `data/videos.json` の representative（url）。
- ブログ公開 → `data/blog.json` の posts に追記（id,title,url,date[,thumb,excerpt]）。
- 旅の記録 → `data/kiroku.json`（lines/municipalities/dormy）。空欄は準備中表示。
- お知らせの定型文 → `data/videos.json` の news_templates。

---

## 7. デプロイ
1. リポジトリ直下に一式を展開（index.html がルート）。
2. Settings → Actions → Workflow permissions を **Read and write**。
3. Settings → Pages で公開ブランチ指定。
4. Actions → Update videos & news → Run workflow を一度実行（初回はIDシード）。

---

## 8. 未確定・情報待ち（次の作業候補）
- ~~プロフィール文（#about .profile）~~ ＝**確定済**（旅を軸にした自己紹介に差し替え）。
- ~~プライバシーポリシー~~ ＝**確定済**（運営者「しゆ」明記／Googleアナリティクス利用を明記。GA計測ID G-CRY661TJ9H を全ページの<head>に設置済）。
- ~~市区町村踏破・名所制覇~~ ＝**実装済**（下記「旅の記録データ源」参照）。
- ~~鉄道乗りつぶし~~ ＝**実装済**（下記「旅の記録データ源」参照。達成率：JR全線91.2%・私鉄全線39.3%）。
- ~~ドーミーイン踏破~~ ＝**実装済**（下記「ドーミーイン踏破」参照。マスター＋訪問の二層＋Issue投稿運用）。訪問は今後スマホから追加。
- ブログ初回記事（blog.json）。
- map1.webp の使い道（未使用）。市区町村は「地図なし・ランキング表示」で確定したため地図用途では不使用。
- カテゴリの見せ方の別案（3.4のメモ）採用可否。

### 旅の記録データ源（kiroku.html）
市区町村踏破と名所制覇は、しゆさんの別ツール（踏破可視化マップ）が生成するJSONをそのまま読んで描画する。**更新方法＝該当JSONを差し替えてコミットするだけ**（サイト側の編集不要）。
- `data/visited_cities.json`：市区町村踏破。meta（totalMunicipalities/visitedCount/coverageRate/dateRange）＋prefectures（47件 name/total/visited/rate）＋cities（JISコード別 name/prefCode…、政令市は「札幌市中央区」形式）。ヘッドライン＋完全踏破県＋**都道府県ランキング（横3列・幅で3→2→1列）**。**都道府県をクリックで、その県の訪問市区町村（政令市は市+区名）を展開**。
- `data/spot_visits.json`：名所制覇。categories（三名泉・三景ほか）＋各spotのfirstVisit(null=未訪問)。ヘッドライン＋カテゴリ別カード＋訪問チップを描画。
- 重い地図geometry（municipalities.topojson）・GPS軌跡（tracks.geojson）・運転経路（routes.json）は**プライバシー配慮で公開しない**（地図表示は不採用のため不要）。
- **鉄道乗りつぶし**：`data/rail.json`（`scripts/build_rail.py` が生成）。**JR**＝会社別バー、**私鉄**＝乗車のある事業者の会社別バー（無ければ区分別にフォールバック）。全国達成率ヘッドライン＋バー、100%は「完乗」バッジ。**会社をクリックで路線内訳（路線別達成率バー）を展開**（rail.json に各社 lines がある場合）。
  - **更新方法**：乗りつぶしオンラインの画面を全選択コピーし、`data/rail_jr_raw.txt`（JR）と `data/rail_pr_raw.txt`（私鉄等）に貼り替えてコミット → GitHub Actions（`build-rail.yml`）が `build_rail.py` を走らせ `rail.json` を自動再生成。
  - build_rail.py はページ先頭の**サマリー表のみ**を解析（会社名/区分 × 営業km/乗車km/未乗km/乗車率）。路線別明細（タブ区切り・折返し・edit/delete等）は読まないので壊れにくい。文字コードは utf-8/cp932 自動判定。
- **ドーミーイン踏破**（二層構造）：
  - `data/dormy_master.json`（全店マスター＝踏破率の母数＆未訪問一覧）… `scripts/build_dormy_master.py` が生成。既定はWikipedia（MediaWiki API・生wikitext）を取得し、店舗名からブランド推定（御宿野乃=nono/PREMIUM/EXPRESS/ラビスタ等=resort/他=dormy）、都道府県→地方、閉館・見出し・説明文は除外。`data/dormy_wiki_raw.txt` があればそれを優先解析（乗りつぶし方式の手動フォールバック）。`meta.totalPin` に数値を入れると踏破率の分母を固定（前回値を保持）。※現状は共立リゾートが少数。`WIKI_TITLES` に記事追加 or raw貼付けで拡充可。
  - `data/dormy_visits.json`（訪問データ）… `scripts/build_dormy_visit.py` が Issueフォーム投稿を解析して追記。店舗名をマスターへ突合（表記ゆれ吸収）、写真を長辺800pxにリサイズして `images/dormy/<id>.jpg` 保存。
  - 描画（kiroku.html）：全体踏破率ヘッドライン＋**3ブランドのアコーディオン**（ドーミーイン{dormy/premium/express}／御宿野乃／共立リゾート、初期全畳み・見出しに「訪問/総数」）。展開で訪問カード（写真・温泉名・サブブランドタグ・初宿泊日・延べ泊数）を地方順に上、未訪問（名前＋所在）を淡く下。visits空でも0%＋全店未訪問で表示。
  - 運用：訪問追加＝GitHub Issueフォーム。「まとめて追加」（複数件・各行写真）「1件追加」（ドロップダウン）「削除」（登録済みを削除）の3種。同じ店舗を再登録すると上書き更新（写真差替・日付変更）。いずれもスマホ可→ `dormy-visit-action.yml` が自動処理・コミット・Issueクローズ。母数更新＝`build-dormy-master.yml`（月1＋手動）。
- kiroku.json は不使用（旧dormy）。

---

## 9. 検証方法（品質確認）
- CSS 括弧バランス：`grep -o '{'`/`'}'` の数一致。
- JS 構文：`node --check js/main.js` 等。
- 実行時：jsdom で index.html のスクリプトを流し、`.inview` 全件表示・
  ヒーロー/カルーセル初期化・エラーゼロを確認（過去チャットで実施）。
- 表示確認は GitHub Pages かローカルサーバ（CDN読込のためオンライン必須）。
  差し替え後は **Ctrl+F5（スーパーリロード）** でキャッシュ回避。

---

## 10. 主な調整履歴（デザイン決定の経緯）- テンプレ由来クレジット（.pr）は**オリジナル実装のため省略**。
- ヒーローは当初「白パネル＋画像」の分割案 → 仕様書に合わせ「画像全面＋左に白の
  斜めグラデ境界」に刷新。境界は波型ではなく**斜め＋ぼかし**。
- inview は jquery.inview がスクロール中に発火不安定 → **IntersectionObserver**へ。
- 表示幅は「中央寄りすぎ」の指摘を受け拡大（最終 `min(94%,1760px)`）。
- カテゴリは skew（斜体化）→ clip-path（正立）→ 白ぼかし帯（下地の縦線露出）→
  **画像を斜めに切って重ねる clip-path 方式**に確定。白/縦線が出ない構成。
- 代表動画サムネは支給画像 → **YouTube自動取得**へ。
- 縦余白は数回にわたり圧縮、コンテンツは画面端寄りに。

---

## 11. ブログ記事の作成フロー（HTML＋自動目次/シェア/前後ナビ）
記事は1記事＝1つのHTMLファイル（`/blog/<スラッグ>.html`）。共通の見た目・目次・
シェア・前後ナビは共通CSS/JSが担うので、**手で書くのはメタ情報と本文だけ**。

手順：
1. `blog/template.html` を複製し `blog/<スラッグ>.html` にする。
2. `<head>` の【…】プレースホルダ（タイトル・要約・canonical・OGP画像）を埋める。
3. `<body data-post-id="<スラッグ>">` を記事のIDに（`data/blog.json` の id と一致）。
4. `.post-head` のタイトル・日付（`<time datetime>` も）・アイキャッチを設定。
   アイキャッチ不要なら `figure.post-hero` ごと削除。
5. `#post-body` に本文を書く：`<h2>`（章）`<h3>`（節）`<p>`、
   `<figure><img><figcaption>`、`<ul>/<ol>`、`<blockquote>` など。
   画像は `/images/blog/` に置き、`/images/blog/xxx.jpg` で参照。
   2枚並べは `<div class="img-row">…</div>`。
6. `data/blog.json` の `posts` **先頭**（新しい順）に1件追記：
   `{ "id","title","url":"/blog/<スラッグ>.html","date","thumb","excerpt" }`
7. 完了。**目次**は本文の h2/h3 から自動生成、**前後ナビ**は blog.json の並び順から
   自動生成、**シェア**（X/LINE/Facebook/コピー）は自動配線される。

Claude運用（推奨）：ユーザーが本文テキストと差し込み画像を渡す → Claudeが
`template.html` に流し込んで `blog/<スラッグ>.html` を生成＋`blog.json` に追記 →
`/images/blog/` に画像を配置 → リポジトリへ。

関連ファイル：`blog/template.html`（雛形）／`css/blog-article.css`／
`js/blog-article.js`／`data/blog.json`。
