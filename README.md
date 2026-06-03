# レシピ管理アプリ

レシピのスクショを Claude Code（標準の画像認識）で解析し、料理名・材料・手順・メモを
自動抽出して管理する個人用アプリです。**API キー不要・追加課金なし**で動作します。

## フォルダ構成

```
recipe-app/
├── inbox/             # 未分析のスクショを入れるフォルダ
├── done/              # 分析済みのスクショ（自動でここへ移動）
├── data/
│   └── recipes.json   # 解析結果の蓄積データ
├── analyze.py         # 抽出したレシピを recipes.json に保存するツール
├── server.py          # 配信用サーバー（HTML と recipes.json を返す）
├── index.html         # フロントエンド（単一ファイル）
└── start.command      # ダブルクリックでサーバー起動
```

inbox（入力）・done（分析済み）・data（結果データ）と性質ごとに分かれているため、
未分析と分析済みのスクショが混ざることはありません。

## セットアップ

1. `pip3 install -r requirements.txt` を実行（flask のみ）
2. `start.command` をダブルクリック
3. 表示された URL（例：`http://192.168.1.5:8080`）をブラウザで開く

## 使い方

### レシピ登録（Mac から）

1. レシピのスクショを `recipe-app/inbox/` に入れる（複数枚で1レシピも可）
2. Claude Code に「**inbox のスクショを解析して**」と伝える
   - Claude Code が画像を読み取り、レシピ情報を抽出
   - `data/recipes.json` に追記し、処理した画像を `done/` へ移動
3. アプリを開き、ホーム画面の「**📥 同期**」ボタンを押す
   - サーバーから新しいレシピを取り込み、一覧に追加されます
   - 料理写真・タグ・メモはアプリ上で編集できます

### レシピ閲覧・管理（iPhone から）

- Mac と iPhone を同じ WiFi に接続
- ターミナルに表示された URL を iPhone Safari で開く
- ホーム画面に追加するとアプリのように使えます

## 仕組み

- **画像解析** は Claude Code 本体のマルチモーダル機能が担当します（Anthropic API は呼びません）。
- `analyze.py` は Claude Code が抽出したレシピを受け取り、`id`・`createdAt` などを付与して
  `data/recipes.json` に保存する役割です。
- アプリ側のデータはブラウザの localStorage に保存され、「📥 同期」で `recipes.json` の
  内容を取り込みます（id が重複するレシピは上書きせず、新規のみ追加）。

## 注意事項

- Mac のサーバーが起動していないと iPhone からアクセス・同期できません。
- アプリのデータはブラウザの localStorage に保存されます（同期元の `recipes.json` とは別管理）。
- 料理写真はセッション中のみ表示されます（リロードで 🍽 に戻ります）。
- アプリは常に同じ URL（`http://localhost:8080` など）で開いてください。localStorage は
  URL（オリジン）ごとに別管理になるためです。
