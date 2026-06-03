#!/usr/bin/env python3
"""inbox/ のスクショから抽出したレシピを data/recipes.json に追記する保存ツール。

画像解析（OCR）は Claude Code 本体（マルチモーダル）が担当する。
このスクリプトは Claude API を呼ばず、抽出済みのレシピJSONを受け取って保存するだけ。
そのため APIキー不要・従量課金なし（Claude Code サブスクリプションの範囲内）で動作する。

運用フロー:
    1. 解析したいスクショを inbox/ に入れる
    2. Claude Code に「inbox のスクショを解析して」と伝える
       → Claude Code が inbox/ の画像を読み取り、レシピ情報を抽出する
       → 抽出した {"title","ingredients","steps","memo"} を標準入力でこのスクリプトに渡す

直接の実行例（標準入力でレシピJSONを渡す）:
    echo '{"title":"...","ingredients":["..."],"steps":["..."],"memo":"..."}' | python3 analyze.py

実行すると:
    - sourceFiles で画像名を指定すればその画像だけを、省略すれば inbox/ の全画像を
      1レシピとして処理する
    - id/cooked/tags/createdAt/updatedAt を付与して data/recipes.json に追記する
    - 処理した画像（sourceFiles）を done/ に移動する

inbox/ に複数レシピのスクショをまとめて入れた場合:
    Claude Code が画像をレシピごとに振り分け、レシピ1件ごとに sourceFiles へ
    該当する画像名を指定して、このスクリプトをレシピの数だけ実行する。
    （指定された画像だけが done/ に移動するので、残りは次のレシピとして処理できる）
"""

import json
import os
import random
import shutil
import sys
import time
from datetime import datetime, timezone

# このファイルが置かれているディレクトリ（recipe-app/）を基準にする
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INBOX_DIR = os.path.join(BASE_DIR, "inbox")
DONE_DIR = os.path.join(BASE_DIR, "done")
DATA_DIR = os.path.join(BASE_DIR, "data")
RECIPES_JSON = os.path.join(DATA_DIR, "recipes.json")

# 対象とする画像拡張子（大文字小文字は判定時に正規化する）
IMAGE_EXTS = (".png", ".jpg", ".jpeg")


def ensure_dirs():
    """inbox/ done/ data/ を用意する（なければ作成する）。"""
    for d in (INBOX_DIR, DONE_DIR, DATA_DIR):
        os.makedirs(d, exist_ok=True)


def find_images():
    """inbox/ 内の画像ファイル名を取得する（ソート済み）。"""
    files = []
    for name in sorted(os.listdir(INBOX_DIR)):
        path = os.path.join(INBOX_DIR, name)
        if os.path.isfile(path) and os.path.splitext(name)[1].lower() in IMAGE_EXTS:
            files.append(name)
    return files


def load_recipes():
    """data/recipes.json を読み込む。無ければ・壊れていれば空配列を返す。"""
    if not os.path.exists(RECIPES_JSON):
        return []
    try:
        with open(RECIPES_JSON, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_recipes(recipes):
    """data/recipes.json に書き出す（日本語はそのまま・整形あり）。"""
    with open(RECIPES_JSON, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)


def move_to_done(filenames):
    """処理済み画像を inbox/ から done/ に移動する。"""
    for name in filenames:
        src = os.path.join(INBOX_DIR, name)
        dst = os.path.join(DONE_DIR, name)
        # done/ に同名がある場合は上書きを避けて連番を付ける
        if os.path.exists(dst):
            base, ext = os.path.splitext(name)
            dst = os.path.join(DONE_DIR, f"{base}_{int(time.time())}{ext}")
        shutil.move(src, dst)


def now_iso():
    """JS の toISOString() と同じ "...Z" 形式（ミリ秒3桁）で現在時刻を返す。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def main():
    ensure_dirs()

    images = find_images()

    # 標準入力から、Claude Codeが抽出した抽出済みレシピJSONを受け取る
    raw = sys.stdin.read().strip()
    if not raw:
        print("レシピJSONが標準入力から渡されていません")
        return
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        print(f"標準入力をJSONとして読み取れませんでした。入力：{raw}")
        return

    # 出典画像と、done/ へ移動する画像を決める。
    # sourceFiles 指定があれば、その画像名を出典として記録する（複数レシピを振り分ける場合に使う）。
    # done/ へ移動するのは inbox/ に実在する画像だけ。
    #   → 同じ画像から複数レシピを作るとき、2件目以降は移動済みでもエラーにせず保存できる。
    specified = parsed.get("sourceFiles")
    if specified:
        source_files = list(specified)
        move_targets = [n for n in specified if n in images]
    else:
        if not images:
            print("inbox/ にスクショが見つかりません")
            return
        source_files = images
        move_targets = images

    now = now_iso()
    recipe = {
        "id": f"recipe_{int(time.time() * 1000)}_{random.random()}",
        "title": str(parsed.get("title", "")),
        "ingredients": [str(x) for x in (parsed.get("ingredients") or [])],
        "steps": [str(x) for x in (parsed.get("steps") or [])],
        "memo": str(parsed.get("memo", "")),
        "tags": [],
        "cooked": False,
        "createdAt": now,
        "updatedAt": now,
        "sourceFiles": source_files,
    }

    # data/recipes.json に追記する
    recipes = load_recipes()
    recipes.append(recipe)
    save_recipes(recipes)

    # inbox/ に実在する画像だけを done/ に移動する
    if move_targets:
        move_to_done(move_targets)

    print(f"✅ 解析完了：「{recipe['title']}」")
    print(f"　 材料 {len(recipe['ingredients'])}件 / 手順 {len(recipe['steps'])}件")
    print(f"　 → data/recipes.json に保存しました（出典画像 {len(source_files)}枚）")
    if move_targets:
        print(f"　 → {len(move_targets)}枚を done/ に移動しました")


if __name__ == "__main__":
    main()
