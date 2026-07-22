#!/usr/bin/env python3
"""Scans v8 validation rounds for the token-cost/latency anomaly (originally
observed once: vault-b t1, 191k cumulative prompt tokens, 33 min) and
reports whether it's a recurring pattern or an isolated outlier.

Usage: python check_cost_spikes.py <results-v8-runs-dir> [--tokens N] [--seconds N]
"""
import json
import sys
from pathlib import Path

CASES = ["baseline", "vault-a", "vault-b"]
TASK_IDS = ["t1", "t2", "t3", "t4", "t5", "t6"]


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "results-v8-runs"
    token_threshold = 80000
    seconds_threshold = 300
    for i, a in enumerate(sys.argv):
        if a == "--tokens" and i + 1 < len(sys.argv):
            token_threshold = int(sys.argv[i + 1])
        if a == "--seconds" and i + 1 < len(sys.argv):
            seconds_threshold = int(sys.argv[i + 1])

    rounds = sorted(d for d in root.glob("round-*") if d.is_dir())
    if not rounds:
        print("nenhuma rodada encontrada em", root)
        return

    rows = []
    for d in rounds:
        for case in CASES:
            for tid in TASK_IDS:
                f = d / case / f"{tid}.json"
                if not f.exists():
                    continue
                r = json.loads(f.read_text(encoding="utf-8"))
                prompt_tok = r.get("tokens", {}).get("prompt_tokens", 0)
                dur = r.get("duration_s", 0)
                actions = len(r.get("retrieval", {}).get("actions", []))
                repairs = r.get("repairs", 0)
                rows.append({
                    "round": d.name, "case": case, "task": tid,
                    "prompt_tokens": prompt_tok, "duration_s": dur,
                    "actions": actions, "repairs": repairs,
                })

    total = len(rows)
    spikes = [r for r in rows
              if r["prompt_tokens"] >= token_threshold or r["duration_s"] >= seconds_threshold]

    print(f"total de execucoes de tarefa analisadas: {total}")
    print(f"limites: prompt_tokens >= {token_threshold} OU duration_s >= {seconds_threshold}")
    print(f"picos encontrados: {len(spikes)} ({100*len(spikes)/total:.1f}% das execucoes)")
    print()
    if spikes:
        print("detalhe dos picos:")
        for s in sorted(spikes, key=lambda r: -r["prompt_tokens"]):
            print(f"  {s['round']}/{s['case']}/{s['task']}: "
                  f"{s['prompt_tokens']} tokens, {s['duration_s']}s, "
                  f"{s['actions']} actions, {s['repairs']} repairs")
    else:
        print("nenhum pico reproduzido — a observacao original parece ter sido outlier isolado.")

    print()
    print("distribuicao de prompt_tokens por caso (media / max):")
    for case in CASES:
        vals = [r["prompt_tokens"] for r in rows if r["case"] == case]
        if vals:
            print(f"  {case}: media={sum(vals)/len(vals):.0f} max={max(vals)}")

    print()
    print("distribuicao de duration_s por caso (media / max):")
    for case in CASES:
        vals = [r["duration_s"] for r in rows if r["case"] == case]
        if vals:
            print(f"  {case}: media={sum(vals)/len(vals):.0f}s max={max(vals)}s")

    print()
    print("correlacao actions vs prompt_tokens (so casos com KB, actions>0):")
    kb_rows = [r for r in rows if r["actions"] > 0]
    if kb_rows:
        for r in sorted(kb_rows, key=lambda x: -x["actions"])[:10]:
            print(f"  {r['round']}/{r['case']}/{r['task']}: actions={r['actions']} "
                  f"tokens={r['prompt_tokens']} dur={r['duration_s']}s")


if __name__ == "__main__":
    main()
