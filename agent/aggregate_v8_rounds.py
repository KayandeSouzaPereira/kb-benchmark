#!/usr/bin/env python3
"""Aggregates v8 rounds (6 tasks incl. t6) — same idea as aggregate_rounds.py
but for the extended-KB benchmark.

Usage: python aggregate_v8_rounds.py <results-v8-runs-dir>
"""
import json
import statistics as stats
import sys
from pathlib import Path

CASES = ["baseline", "vault-a", "vault-b"]
LABELS = {"baseline": "C — No KB", "vault-a": "A — Structured", "vault-b": "B — Zettelkasten"}
TASK_IDS = ["t1", "t2", "t3", "t4", "t5", "t6"]


def mean_std(vals):
    if not vals:
        return (None, None)
    m = stats.mean(vals)
    s = stats.pstdev(vals) if len(vals) > 1 else 0.0
    return (m, s)


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results-v8-runs")
    rounds = sorted(d for d in root.glob("round-*") if d.is_dir())

    case_totals = {c: [] for c in CASES}
    task_scores = {c: {t: [] for t in TASK_IDS} for c in CASES}
    for d in rounds:
        for case in CASES:
            total_p = total_t = 0
            for tid in TASK_IDS:
                f = d / case / f"{tid}.json"
                if not f.exists():
                    continue
                r = json.loads(f.read_text(encoding="utf-8"))
                task_scores[case][tid].append(r["passed"])
                total_p += r["passed"]
                total_t += r["total"]
            if total_t:
                case_totals[case].append(total_p)

    print(f"rounds: {[d.name for d in rounds]}  n={len(rounds)}")
    print()
    print(f"{'round':<10}" + "".join(f"{LABELS[c]:<20}" for c in CASES))
    for i, d in enumerate(rounds):
        row = f"{d.name:<10}"
        for c in CASES:
            v = case_totals[c][i] if i < len(case_totals[c]) else None
            row += f"{v}/37{'':<15}" if v is not None else f"{'—':<20}"
        print(row)
    print()
    for c in CASES:
        m, s = mean_std(case_totals[c])
        mn, mx = min(case_totals[c]), max(case_totals[c])
        wins = None
        print(f"{LABELS[c]}: {m:.1f} ± {s:.1f} / 37  (min {mn}, max {mx})")

    # how often does B beat A outright, per round
    a_wins = b_wins = ties = 0
    for i in range(len(rounds)):
        a, b = case_totals["vault-a"][i], case_totals["vault-b"][i]
        if a > b:
            a_wins += 1
        elif b > a:
            b_wins += 1
        else:
            ties += 1
    print(f"\nA vence em {a_wins}/{len(rounds)} rodadas, B vence em {b_wins}/{len(rounds)}, empates: {ties}")

    print("\nPor tarefa (media A vs B):")
    for tid in TASK_IDS:
        ma, _ = mean_std(task_scores["vault-a"][tid])
        mb, _ = mean_std(task_scores["vault-b"][tid])
        print(f"  {tid}: A={ma:.2f}  B={mb:.2f}")


if __name__ == "__main__":
    main()
