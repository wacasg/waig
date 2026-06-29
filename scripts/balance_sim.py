#!/usr/bin/env python3
"""WAIG「店長を救え！」バランス・シミュレータ.

index.html から CONFIG・calcYen の係数・イベント効果(eff)・開始市場レンジを直接
パースして読み取り、モンテカルロでクリア率／平均売上／ランク分布を戦略別に出す。
コードを直接読むので、index.html を編集すれば結果も自動で追従する（数値の二重管理なし）。

使い方:
    python3 scripts/balance_sim.py
    python3 scripts/balance_sim.py --games 50000
    python3 scripts/balance_sim.py --json
"""
from __future__ import annotations
import argparse
import itertools
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"

CIRCLED = {"①": 0, "②": 1, "③": 2}  # ① ② ③ → slot index


def parse_index(text: str) -> dict:
    """index.html からバランス計算に必要な定数とイベントを抽出する。"""
    def need(pattern: str, label: str, group=1, cast=float):
        m = re.search(pattern, text)
        if not m:
            sys.exit(f"[balance_sim] index.html から {label} を読み取れませんでした。"
                     " パターン変更が必要かもしれません。")
        return cast(m.group(group))

    yen_factor = need(r"const\s+YEN_FACTOR\s*=\s*(\d+)", "YEN_FACTOR", cast=int)
    target = need(r"target\s*:\s*(\d+)", "target (CONFIG)", cast=int)

    # calcYen の重み: 0.34*s.kya + 0.33*s.tsu + 0.33*s.kai
    w = re.findall(r"([0-9.]+)\s*\*\s*s\.(kya|tsu|kai)", text)
    weights = {k: float(v) for v, k in w}
    for k in ("kya", "tsu", "kai"):
        weights.setdefault(k, 1 / 3)
    # bottleneck: 0.6 + 0.4*(min/100)
    bm = re.search(r"([0-9.]+)\s*\+\s*([0-9.]+)\s*\*\s*\(\s*Math\.min", text)
    bottleneck = (float(bm.group(1)), float(bm.group(2))) if bm else (0.6, 0.4)

    # 開始市場: vals = [rnd(62,74), rnd(44,55), rnd(42,53)]
    sm = re.search(r"vals\s*=\s*\[\s*rnd\((\d+),(\d+)\)\s*,\s*rnd\((\d+),(\d+)\)\s*,"
                   r"\s*rnd\((\d+),(\d+)\)\s*\]", text)
    if not sm:
        sys.exit("[balance_sim] startMarket のレンジを読み取れませんでした。")
    nums = list(map(int, sm.groups()))
    start_ranges = [(nums[0], nums[1]), (nums[2], nums[3]), (nums[4], nums[5])]

    # イベント抽出: "今月の出来事 ①/②/③" を区切りにチャンク化
    chunks = re.split(r'tag:"今月の出来事\s*(.)"', text)
    # chunks = [前文, slotchar, body, slotchar, body, ...]
    slots: list[list[dict]] = [[], [], []]
    for i in range(1, len(chunks), 2):
        slot_char = chunks[i]
        body = chunks[i + 1]
        slot_idx = CIRCLED.get(slot_char)
        if slot_idx is None:
            continue
        # 次の event の actions まで（このチャンクは次のtagまでなので body 全体でOK）
        rec = re.search(r'aiRec:"([ABC])"', body)
        ai_rec = rec.group(1) if rec else "A"
        actions = {}
        for am in re.finditer(r'id:"([ABC])"[^}]*?eff:\{([^}]*)\}', body):
            aid = am.group(1)
            eff = {}
            for pm in re.finditer(r"(kya|tsu|kai)\s*:\s*(-?\d+)", am.group(2)):
                eff[pm.group(1)] = int(pm.group(2))
            actions[aid] = eff
        if actions:
            slots[slot_idx].append({"aiRec": ai_rec, "actions": actions})

    for i, s in enumerate(slots):
        if not s:
            sys.exit(f"[balance_sim] スロット{i + 1} のイベントを抽出できませんでした。")

    return {
        "yen_factor": yen_factor, "target": target, "weights": weights,
        "bottleneck": bottleneck, "start_ranges": start_ranges, "slots": slots,
    }


def clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


def calc_yen(s: dict, cfg: dict) -> int:
    w = cfg["weights"]
    ws = w["kya"] * s["kya"] + w["tsu"] * s["tsu"] + w["kai"] * s["kai"]
    b0, b1 = cfg["bottleneck"]
    bottleneck = b0 + b1 * (min(s["kya"], s["tsu"], s["kai"]) / 100)
    return round(ws * bottleneck * cfg["yen_factor"])


def apply(state: dict, eff: dict) -> dict:
    ns = dict(state)
    for k, v in eff.items():
        ns[k] = clamp(ns[k] + v)
    return ns


def start_market(cfg: dict) -> dict:
    vals = [random.randint(a, b) for a, b in cfg["start_ranges"]]
    random.shuffle(vals)
    return {"kya": vals[0], "tsu": vals[1], "kai": vals[2]}


def rank_of(final_yen: int, target: int) -> str:
    r = final_yen / target
    if r >= 1.05:
        return "S"
    if r >= 1.0:
        return "A"
    if r >= 0.9:
        return "B"
    return "C"


def play(cfg: dict, events: list[dict], strategy: str) -> dict:
    state = start_market(cfg)
    if strategy == "optimal":
        best = None
        for path in itertools.product("ABC", repeat=3):
            s = state
            for ev, choice in zip(events, path):
                s = apply(s, ev["actions"].get(choice, {}))
            y = calc_yen(s, cfg)
            if best is None or y > best:
                best = y
        return {"yen": best}
    for ev in events:
        if strategy == "ai":
            choice = ev["aiRec"]
        elif strategy == "random":
            choice = random.choice(list(ev["actions"].keys()))
        elif strategy == "weakfix":  # 最小メーターを最も伸ばす手
            mkey = min(state, key=state.get)
            choice = max(ev["actions"],
                         key=lambda a: ev["actions"][a].get(mkey, 0))
        else:
            choice = ev["aiRec"]
        state = apply(state, ev["actions"][choice])
    return {"yen": calc_yen(state, cfg)}


STRATEGIES = {
    "ai": "AI全追従",
    "weakfix": "弱点補強",
    "optimal": "最適（理論上限）",
    "random": "ランダム",
}


def run(cfg: dict, games: int) -> dict:
    target = cfg["target"]
    results = {k: {"clear": 0, "yen_sum": 0, "ranks": {"S": 0, "A": 0, "B": 0, "C": 0}}
               for k in STRATEGIES}
    for _ in range(games):
        events = [random.choice(slot) for slot in cfg["slots"]]
        for strat in STRATEGIES:
            out = play(cfg, events, strat)
            y = out["yen"]
            r = results[strat]
            r["yen_sum"] += y
            if y >= target:
                r["clear"] += 1
            r["ranks"][rank_of(y, target)] += 1
    summary = {}
    for strat, r in results.items():
        summary[strat] = {
            "label": STRATEGIES[strat],
            "clear_rate": r["clear"] / games,
            "avg_yen": round(r["yen_sum"] / games),
            "ranks": {k: v / games for k, v in r["ranks"].items()},
        }
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description="WAIG バランス・シミュレータ")
    ap.add_argument("--games", type=int, default=20000, help="試行回数 (default 20000)")
    ap.add_argument("--seed", type=int, default=None, help="乱数シード（再現用）")
    ap.add_argument("--json", action="store_true", help="JSON で出力")
    args = ap.parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    if not INDEX.exists():
        sys.exit(f"[balance_sim] {INDEX} が見つかりません。")
    cfg = parse_index(INDEX.read_text(encoding="utf-8"))
    summary = run(cfg, args.games)

    if args.json:
        print(json.dumps({"target": cfg["target"], "games": args.games,
                          "strategies": summary}, ensure_ascii=False, indent=2))
        return

    print(f"\n=== WAIG バランス・シミュレーション ===")
    print(f"売上目標(target): ¥{cfg['target']:,} / 試行: {args.games:,} 回\n")
    print(f"{'戦略':<16}{'クリア率':>9}{'平均売上':>12}   ランク分布(S/A/B/C)")
    print("-" * 64)
    for strat in ("optimal", "weakfix", "ai", "random"):
        s = summary[strat]
        rk = s["ranks"]
        print(f"{s['label']:<16}{s['clear_rate']*100:>7.1f}% ¥{s['avg_yen']:>10,}   "
              f"{rk['S']*100:>4.0f}/{rk['A']*100:>3.0f}/{rk['B']*100:>3.0f}/{rk['C']*100:>3.0f}")
    print()
    ai = summary["ai"]["clear_rate"] * 100
    opt = summary["optimal"]["clear_rate"] * 100
    notes = []
    if not (45 <= ai <= 70):
        notes.append(f"⚠️ AI全追従のクリア率 {ai:.1f}% が目安(45–70%)から外れています。")
    if opt < 85:
        notes.append(f"⚠️ 最適戦略のクリア率 {opt:.1f}% が低め(目安85%+)。考えた子が報われにくい。")
    if not notes:
        notes.append("✅ クリア率は目安レンジ内です。")
    for n in notes:
        print(n)
    print()


if __name__ == "__main__":
    main()
