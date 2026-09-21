# Work Base（ベースサイト）

北山さんの仕事の基地。よく使うものが 1 画面に集まり、必要な情報（通知）が流れ込んでくる場所。
ゆくゆくは中央下の対話窓からオリジナル AI につながる想定。

## 画面構成（v2）

| 位置 | 中身 |
|---|---|
| 中央 | Work Cosmos（力学グラフ）。常にゆっくり回転し、中心から信号が流れ続ける。星クリックでツールを開く |
| 左上 | Notion「今週の作業板」の完了済みタスク数。クリックで Notion へ |
| 右上 | 教育・出版ニュース（タブ切替）。毎時自動更新 |
| 左下 | よく使う Google（Gmail が一番上）＋「編集中」フォルダ検索 |
| 右下 | Amazon ランキング・honto・他社出版社 |
| 中央下 | 対話窓（今は形だけ）。星の名前を打つと光る／「〜を開いて」で開く／「全画面」「リセット」 |

全画面：上部の ⛶ ボタン、F キー、背景ダブルクリック。
Chrome で「アプリとしてインストール」すると全画面のアプリとして起動できる（Surface 向け）。

## ファイル

| ファイル | 役割 |
|---|---|
| `index.html` | 本体（ツール一覧は `<script>` 冒頭の `TOOLS` を直す） |
| `data/news.json` | ニュース（自動生成） |
| `data/notion.json` | 完了数（自動生成。`history` に日ごとの件数） |
| `scripts/update.py` | 上 2 つを作るスクリプト（標準ライブラリのみ） |
| `.github/workflows/update.yml` | GitHub Actions で毎時 `update.py` を実行してコミット |
| `manifest.webmanifest` / `icon.svg` | アプリとしてインストールする用 |

## 公開（GitHub Pages）

- リポジトリ：`kitayamatoshiomi/kitayamatoshiomi.github.io` → URL は https://kitayamatoshiomi.github.io/
- 公開サイトなので誰でも見られる。載っているのはツールの URL（Drive フォルダ ID を含む）と完了件数のみ。Drive 側の共有は「制限付き」のままにしておくこと。

## Notion 完了数を自動更新するには（1 回だけ）

1. https://www.notion.so/my-integrations で「新しいインテグレーション」（内部）を作り、シークレットをコピー
2. Notion の「📋 今週の作業板」ページ右上 … →「接続」→ 作ったインテグレーションを追加
3. GitHub のリポジトリ → Settings → Secrets and variables → Actions → New repository secret
   名前 `NOTION_TOKEN`、値にシークレットを貼る

設定するまでは、9/21 時点の件数（485）が表示されたまま。

## 開発ログ

`開発記録.md` を参照。
