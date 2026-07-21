#!/usr/bin/env python3
"""Agrega N rodadas independentes do benchmark (mesma config) em estatisticas
de confirmacao: media, desvio padrao, min/max por tarefa e por caso.

Uso: python aggregate_rounds.py <results-v7-runs-dir> [--out results-v7-runs/AGGREGATE.md]
"""
import json
import statistics as stats
import sys
from pathlib import Path

CASES = ["baseline", "vault-a", "vault-b"]
LABELS = {
    "baseline": "C — No KB",
    "vault-a": "A — Structured vault",
    "vault-b": "B — Zettelkasten",
}
TASK_IDS = ["t1", "t2", "t3", "t4", "t5"]


def load_rounds(root: Path):
    rounds = []
    for d in sorted(root.glob("round-*")):
        if not d.is_dir():
            continue
        data = {}
        ok = True
        for case in CASES:
            data[case] = {}
            for tid in TASK_IDS:
                f = d / case / f"{tid}.json"
                if not f.exists():
                    ok = False
                    continue
                data[case][tid] = json.loads(f.read_text(encoding="utf-8"))
        if ok:
            rounds.append((d.name, data))
        else:
            print(f"aviso: {d.name} incompleta, ignorada")
    return rounds


def mean_std(vals):
    if not vals:
        return (None, None)
    m = stats.mean(vals)
    s = stats.pstdev(vals) if len(vals) > 1 else 0.0
    return (m, s)


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "results-v7-runs"
    out_path = root / "AGGREGATE.md"
    for i, a in enumerate(sys.argv):
        if a == "--out" and i + 1 < len(sys.argv):
            out_path = Path(sys.argv[i + 1])

    rounds = load_rounds(root)
    n = len(rounds)
    if n == 0:
        print("nenhuma rodada completa encontrada em", root)
        return

    lines = [f"# v7 statistical confirmation — {n} independent rounds", ""]
    lines.append(f"Rounds used: {', '.join(r[0] for r in rounds)}")
    lines.append("")

    # ---- per task per case ----
    lines.append("## Score per task (mean ± stdev across rounds, out of task total)")
    lines.append("")
    header = "| Task | " + " | ".join(LABELS[c] for c in CASES) + " |"
    lines.append(header)
    lines.append("|---|" + "---|" * len(CASES))

    task_totals = {c: {} for c in CASES}
    compile_rates = {c: {} for c in CASES}
    for tid in TASK_IDS:
        row = [f"| {tid}"]
        for case in CASES:
            passed_vals = [rd[case][tid]["passed"] for _, rd in rounds if tid in rd[case]]
            total_vals = [rd[case][tid]["total"] for _, rd in rounds if tid in rd[case]]
            compiled_vals = [1 if rd[case][tid].get("compiled") else 0 for _, rd in rounds if tid in rd[case]]
            m, s = mean_std(passed_vals)
            t = total_vals[0] if total_vals else 0
            task_totals[case][tid] = (passed_vals, t)
            cr, _ = mean_std(compiled_vals)
            compile_rates[case][tid] = cr
            row.append(f"{m:.1f}±{s:.1f}/{t}" if m is not None else "—")
        lines.append(" | ".join(row) + " |")

    lines.append("")
    lines.append("## Compile rate per task (fraction of rounds that compiled)")
    lines.append("")
    lines.append(header)
    lines.append("|---|" + "---|" * len(CASES))
    for tid in TASK_IDS:
        row = [f"| {tid}"]
        for case in CASES:
            cr = compile_rates[case][tid]
            row.append(f"{cr*100:.0f}%" if cr is not None else "—")
        lines.append(" | ".join(row) + " |")

    # ---- per case totals across all 31 tests ----
    lines.append("")
    lines.append("## Total score per round (sum of all 31 tests)")
    lines.append("")
    lines.append("| Round | " + " | ".join(LABELS[c] for c in CASES) + " |")
    lines.append("|---|" + "---|" * len(CASES))
    case_round_totals = {c: [] for c in CASES}
    for name, rd in rounds:
        row = [f"| {name}"]
        for case in CASES:
            p = sum(rd[case][tid]["passed"] for tid in TASK_IDS if tid in rd[case])
            t = sum(rd[case][tid]["total"] for tid in TASK_IDS if tid in rd[case])
            case_round_totals[case].append(p)
            row.append(f"{p}/{t}")
        lines.append(" | ".join(row) + " |")

    lines.append("")
    total_of = sum(task_totals["baseline"][tid][1] for tid in TASK_IDS)
    lines.append(f"| **Mean ± stdev** | " + " | ".join(
        f"{mean_std(case_round_totals[c])[0]:.1f}±{mean_std(case_round_totals[c])[1]:.1f}/{total_of}"
        for c in CASES) + " |")
    lines.append(f"| **Min–Max** | " + " | ".join(
        f"{min(case_round_totals[c])}–{max(case_round_totals[c])}" for c in CASES) + " |")

    # ---- retrieval gold-hit rate ----
    lines.append("")
    lines.append("## Gold-note hit rate (mean ± stdev across rounds, KB cases only)")
    lines.append("")
    lines.append("| Case | Mean gold-hit rate | Stdev |")
    lines.append("|---|---|---|")
    for case in ("vault-a", "vault-b"):
        vals = []
        for _, rd in rounds:
            for tid in TASK_IDS:
                t = rd[case].get(tid)
                if t and t["retrieval"].get("gold_hit_rate") is not None:
                    vals.append(t["retrieval"]["gold_hit_rate"])
        m, s = mean_std(vals)
        lines.append(f"| {LABELS[case]} | {m:.2f} | {s:.2f} |" if m is not None else f"| {LABELS[case]} | — | — |")

    # ---- simple significance check: does A's mean total exceed B's by more than 1 stdev? ----
    lines.append("")
    lines.append("## A vs B: is the difference significant?")
    lines.append("")
    ma, sa = mean_std(case_round_totals["vault-a"])
    mb, sb = mean_std(case_round_totals["vault-b"])
    mc, sc = mean_std(case_round_totals["baseline"])
    diff = ma - mb
    pooled = ((sa ** 2 + sb ** 2) / 2) ** 0.5 if n > 1 else 0
    lines.append(f"- A (structured vault): {ma:.1f} ± {sa:.1f} (n={n})")
    lines.append(f"- B (Zettelkasten): {mb:.1f} ± {sb:.1f} (n={n})")
    lines.append(f"- C (no KB): {mc:.1f} ± {sc:.1f} (n={n})")
    lines.append(f"- A − B = {diff:+.1f} points; pooled stdev = {pooled:.1f}")
    if pooled > 0:
        lines.append(f"- Effect size (A−B)/pooled_stdev ≈ {diff/pooled:.2f} "
                      f"({'noise-level, within run-to-run variance' if abs(diff) < pooled else 'exceeds one pooled stdev — likely a real effect'})")
    lines.append(f"- KB (avg of A,B) vs no-KB gap: {(ma+mb)/2 - mc:+.1f} points "
                  f"— {'far exceeds' if (ma+mb)/2 - mc > max(sa,sb,sc)*2 else 'exceeds'} run-to-run noise")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_path}")
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
