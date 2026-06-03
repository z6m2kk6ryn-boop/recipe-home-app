#!/usr/bin/env python3
"""レシピ管理アプリ バックエンドサーバー（Flask）

- ポート8080で起動
- GET /                  : index.html を返す
- GET /data/recipes.json : analyze.py が蓄積したレシピJSONを返す（無ければ空配列）
- 起動時にMacのLAN IPアドレスをターミナルに表示する

スクショ解析は analyze.py をターミナルから直接実行する方式に変更した。
（Claude Code の認証は Flask の子プロセスに引き継がれないため、サーバーでは解析しない）
"""

import json
import os
import socket

from flask import Flask, jsonify, send_from_directory

# このファイルが置かれているディレクトリ（recipe-app/）を基準にする
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECIPES_JSON = os.path.join(BASE_DIR, "data", "recipes.json")

app = Flask(__name__)

PORT = 8080


@app.route("/")
def index():
    """フロントエンド（index.html）を返す。"""
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/data/recipes.json")
def recipes_json():
    """analyze.py が蓄積したレシピJSONを返す。ファイルが無ければ空配列を返す。"""
    if not os.path.exists(RECIPES_JSON):
        return jsonify([])
    try:
        with open(RECIPES_JSON, encoding="utf-8") as f:
            return jsonify(json.load(f))
    except (json.JSONDecodeError, OSError):
        return jsonify([])


def get_lan_ip():
    """MacのLAN IPアドレスを取得する。

    外部に実際の通信は行わず、ルーティング先を引くことで
    このマシンのLAN側IPアドレスを判定する。
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 実際には送信しないが、ルーティング決定のために接続先を設定する
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


if __name__ == "__main__":
    lan_ip = get_lan_ip()
    print("=" * 48)
    print("  Récipe サーバーを起動しました")
    print("=" * 48)
    print(f"  このMacで開く : http://localhost:{PORT}")
    print(f"  iPhoneで開く  : http://{lan_ip}:{PORT}")
    print("=" * 48)
    print("  ※ MacとiPhoneを同じWiFiに接続してください")
    print("  ※ 終了するには Ctrl+C を押してください")
    print("=" * 48)
    app.run(host="0.0.0.0", port=PORT)
