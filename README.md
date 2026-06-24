# 店長を救え！ — WAIG 意思決定ゲーム

AI・デジタルビジネス学科の体験用ミニゲーム（外部依存なしの単一HTML）。
GitHub Pages で公開しています。

## 公開URL
**https://wacasg.github.io/waig/**

## フォルダの中身
| ファイル | 役割 |
|---|---|
| `index.html` | **公開版（改良済み）**。GitHub Pages がこれを配信します。編集するのはこのファイル。 |
| `tencho_save_me.html` | **元ファイルのバックアップ**（改良前のオリジナル）。動作には使いません。 |
| `README.md` | この説明ファイル。 |

> ⚠️ ゲームのロジック・計算・デザインは原則そのまま。設定変更は基本 `index.html` 内の `CONFIG` を編集します。

## 設定（CONFIG）
`index.html` の先頭付近にある `const CONFIG = { … }` で調整します。

- `applyURL` … 申し込み／問い合わせフォームのURL（空にするとボタン非表示）
  - 現在: `https://forms.gle/x6G5tob4ekWYkhop9`（Googleフォーム「意思決定ゲーム 体験のお問い合わせ」）
- `realGameURL` … 「本物のゲームを見る」リンク先
- `target` … 売上目標（円）
- `schoolName` / `date` / `place` / `applyText` … 現在は結果画面で未使用（バナーを学科案内に差し替えたため）

## これまでの改良点（index.html）
1. 選択肢ボタンに **A / B / C のバッジ**を表示（AIの「Aをおすすめ」の根拠が一目で分かる）。
2. 結果画面のバナーを **オープンキャンパス・出張授業の案内**に差し替え。
   - 「日本経済大学 AI・DB学科」は[学科ページ](https://shibuya.jue.ac.jp/lp/digital-business-management/)へ**別ウィンドウ**リンク。
3. 申込ボタンの文言を **「オープンキャンパス・授業について問い合わせる」** に変更。
4. 表記を **「OC」→「オープンキャンパス」** に統一。

## ローカルで確認する
ビルド不要。`index.html` をブラウザで直接開くか、簡易サーバで配信：

```bash
cd WAIG
python3 -m http.server 8765
# ブラウザで http://localhost:8765/ を開く
```

## デプロイ（GitHub Pages）
`main` ブランチの `/`（root）から配信。`index.html` を編集して push すると数分で反映されます。

```bash
git add index.html
git commit -m "変更内容"
git push origin main
```
