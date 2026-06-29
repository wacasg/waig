---
description: 変更を main に push して GitHub Pages へ反映する
argument-hint: "[コミットメッセージ]"
---

`index.html` の変更を GitHub Pages（`main` ブランチ root 配信）へ反映する。

**push 前チェック（必須）:**
1. `git status` と `git diff` で変更内容を確認し、ユーザーに要約を見せる。
2. まだローカル確認していなければ `/preview` 相当の動作確認を促す（3ターン通し・A/B/C・コンソールエラー無し）。
3. 外部依存（CDN/Webフォント/解析タグ等）が混入していないか確認（単一HTML制約・CLAUDE.md §1）。

**実行:**
```bash
git add -A
git commit -m "$ARGUMENTS"   # 引数が空なら変更内容から簡潔な日本語メッセージを提案して確認を取る
git push origin main
```

push 後:
- 「数分後に https://wacasg.github.io/waig/ に反映される」と案内する。
- 反映確認したい場合は Pages の URL を開いて確認する旨を伝える。

> 注意: `main` 直 push の小規模プロジェクト。大きな変更は事前にブランチ（`feat/...`）を勧める。
> コミット/push はユーザーが明示的に依頼したときのみ実行する。
