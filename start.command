#!/bin/bash
# ダブルクリックでレシピ管理アプリを起動するスクリプト

# このスクリプトが置かれているディレクトリ（recipe-app/）に移動する
cd "$(dirname "$0")" || exit 1

# Flaskサーバーを起動する
python3 server.py
