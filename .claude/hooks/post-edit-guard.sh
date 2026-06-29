#!/usr/bin/env bash
# post-edit-guard.sh — Write/Edit 後の単一HTML・外部依存ガード（CLAUDE.md §1）
#   index.html に外部依存（CDN/Webフォント/外部script・stylesheet）が混入したら
#   stderr で警告し exit 2（Claude にフィードバックされる）。
# settings.json の hooks.PostToolUse (matcher: Write|Edit|MultiEdit) に登録。
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# stdin の JSON を変数に取り込む（heredoc が python の stdin を奪うため env で渡す）
HOOK_INPUT="$(cat)"
export HOOK_INPUT REPO_ROOT

python3 - <<'PY'
import json, re, sys, os

try:
    data = json.loads(os.environ.get("HOOK_INPUT", ""))
except Exception:
    sys.exit(0)

repo_root = os.environ.get("REPO_ROOT", ".")
ti = data.get("tool_input", {}) or {}
path = ti.get("file_path") or ti.get("path") or ""
if not path or os.path.basename(path) != "index.html":
    sys.exit(0)

target = path if os.path.isabs(path) else os.path.join(repo_root, path)
try:
    with open(target, encoding="utf-8") as f:
        html = f.read()
except Exception:
    sys.exit(0)

problems = []
# 外部 script src / link href（http(s):// または protocol-relative //）
for m in re.finditer(r'<(script|link)\b[^>]*\b(src|href)\s*=\s*["\'](https?:)?//[^"\']+', html, re.I):
    # 本文リンク <a href> は対象外（script/link タグのみを検査）
    problems.append(f"外部 {m.group(1)} 読み込み: {m.group(0)[:80]}")
# @import で外部CSS
for m in re.finditer(r'@import\s+(url\()?["\']?(https?:)?//', html, re.I):
    problems.append(f"@import で外部CSS: {m.group(0)[:60]}")
# 代表的なCDN/Webフォント
for kw in ("fonts.googleapis.com", "fonts.gstatic.com", "cdn.jsdelivr.net",
           "unpkg.com", "cdnjs.cloudflare.com", "code.jquery.com"):
    if kw in html:
        problems.append(f"CDN/外部フォント参照: {kw}")

if problems:
    sys.stderr.write(
        "⚠️ [post-edit-guard] index.html に外部依存が混入しています"
        "（単一HTML制約・CLAUDE.md §1 違反）:\n")
    for p in problems:
        sys.stderr.write(f"  - {p}\n")
    sys.stderr.write("外部依存を取り除き、ファイル単体で動く状態に戻してください。\n")
    sys.exit(2)
sys.exit(0)
PY
