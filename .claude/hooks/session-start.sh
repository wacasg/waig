#!/usr/bin/env bash
# session-start.sh — WAIG セッション開始フック
#   1. リモートの変更を取り込む（main / ff-only）
#   2. 作業ツリーの状態を表示
# settings.json の hooks.SessionStart に登録。
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT" || exit 0

echo ""
echo "=== [session-start] WAIG 店長を救え！ ==="

if git rev-parse --git-dir > /dev/null 2>&1; then
  echo "[1/2] git pull --ff-only origin main ..."
  if git pull --ff-only origin main 2>&1 | sed 's/^/      /'; then
    :
  else
    echo "      ⚠️  pull に失敗（未コミットの変更 or 分岐の可能性）。git status を確認してください。"
  fi
  echo "[2/2] 作業ツリー:"
  git status -sb 2>&1 | sed 's/^/      /'
else
  echo "[!] git リポジトリではありません。"
fi

echo "    公開: https://wacasg.github.io/waig/ | 確認: /preview | デプロイ: /deploy"
echo "========================================="
exit 0
