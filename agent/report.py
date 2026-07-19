#!/usr/bin/env python3
"""Gera results/report.md comparando os casos executados."""
import json
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results"
CASES = ["vault-a", "vault-b", "baseline"]
LABELS = {
    "vault-a": "A — Vault estruturado p/ agentes",
    "vault-b": "B — Zettelkasten clássico",
    "baseline": "C — Sem knowledge base",
}


def load():
    data = {}
    for case in CASES:
        d = RESULTS / case
        if not d.is_dir():
            continue
        data[case] = {
            j.stem: json.loads(j.read_text(encoding="utf-8"))
            for j in sorted(d.glob("t*.json")) if "_" not in j.stem
        }
    return data


def pct(passed, total):
    return f"{passed}/{total} ({100 * passed / total:.0f}%)" if total else "—"


def main():
    data = load()
    if not data:
        print("nenhum resultado em", RESULTS)
        return

    task_ids = sorted({tid for case in data.values() for tid in case})
    lines = ["# Benchmark de knowledge base — relatório", ""]
    lines.append("| Tarefa | " + " | ".join(LABELS[c] for c in data) + " |")
    lines.append("|---|" + "---|" * len(data))
    for tid in task_ids:
        row = [f"| {tid}"]
        for case in data:
            r = data[case].get(tid)
            if not r:
                row.append("—")
            else:
                cell = pct(r["passed"], r["total"])
                if not r["compiled"]:
                    cell += " ⚠não compilou"
                row.append(cell)
        lines.append(" | ".join(row) + " |")

    lines.append("| **Total** | " + " | ".join(
        pct(sum(r["passed"] for r in data[c].values()),
            sum(r["total"] for r in data[c].values())) for c in data) + " |")

    lines += ["", "## Retrieval e custo", ""]
    lines.append("| Métrica | " + " | ".join(LABELS[c] for c in data) + " |")
    lines.append("|---|" + "---|" * len(data))

    def agg(case, fn):
        vals = [fn(r) for r in data[case].values() if fn(r) is not None]
        return sum(vals) / len(vals) if vals else None

    rows = [
        ("Ações de retrieval (média)", lambda r: len(r["retrieval"]["actions"])),
        ("Notas lidas (média)", lambda r: len(r["retrieval"]["notes_read"])),
        ("Acerto de notas-ouro (média)", lambda r: r["retrieval"]["gold_hit_rate"]),
        ("Tokens de prompt (média)", lambda r: r["tokens"]["prompt_tokens"]),
        ("Duração por tarefa (s, média)", lambda r: r["duration_s"]),
        ("Reparos de compilação (média)", lambda r: r.get("repairs", 0)),
        ("Tarefas que compilaram", lambda r: 1 if r["compiled"] else 0),
    ]
    for label, fn in rows:
        cells = []
        for case in data:
            v = agg(case, fn)
            cells.append("—" if v is None else f"{v:.2f}")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")

    lines += ["", "## Detalhe por teste", ""]
    for tid in task_ids:
        lines.append(f"### {tid}")
        for case in data:
            r = data[case].get(tid)
            if not r:
                continue
            lines.append(f"- **{LABELS[case]}**: " + (
                r["error"].splitlines()[0] if r["error"] else ", ".join(
                    ("✅" if t["passed"] else "❌") + " " + t["name"]
                    for t in r["tests"])))
        lines.append("")

    out = RESULTS / "report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"relatório: {out}")
    print("\n".join(lines[:20]))


if __name__ == "__main__":
    main()
