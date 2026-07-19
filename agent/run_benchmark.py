#!/usr/bin/env python3
"""Runner do benchmark de knowledge base.

Roda dentro do container. Para cada tarefa: monta workspace a partir do
scaffold, deixa o modelo explorar a vault (protocolo ACTION), escreve os
arquivos gerados e avalia com testes automatizados.

Env:
  CASE        vault-a | vault-b | baseline   (obrigatorio)
  MODEL       default qwen3:8b
  OLLAMA_URL  default http://host.docker.internal:11434
  TASK_FILTER lista de ids separada por virgula (opcional)
  SMOKE=1     apenas valida conectividade e sai
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

BENCH = Path(os.environ.get("BENCH_DIR", "/bench"))
CASE = os.environ.get("CASE", "baseline")
MODEL = os.environ.get("MODEL", "qwen3:8b")
OLLAMA = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434").rstrip("/")
SCAFFOLD = Path(os.environ.get("SCAFFOLD_DIR", "/opt/scaffold"))
WORK = Path(os.environ.get("WORK_DIR", "/work")) / CASE
VAULT = BENCH / "knowledge" / CASE
RESULTS = BENCH / "results" / CASE
TASKS_DIR = BENCH / "tasks"
EVAL_DIR = BENCH / "eval"

MAX_ACTIONS = 8
MAX_NUDGES = 2
MAX_REPAIRS = 3
NUM_CTX = 16384
TEMPERATURE = 0.2

FILE_RE = re.compile(r"FILE:\s*([^\n`]+?)\s*\n```[a-zA-Z]*\s*\n(.*?)```", re.S)
ACTION_RE = re.compile(r"^ACTION:\s*(ls|grep|read)\s*(.*)$", re.M)

SYSTEM_VAULT = """Você é um engenheiro de software sênior de um time de produto.
O time mantém uma base de conhecimento em arquivos Markdown com as regras de
negócio e convenções. Você DEVE consultá-la antes de escrever código, porque
as regras específicas do produto não são óbvias.

Para explorar a base, responda com UMA única linha de comando por mensagem:

ACTION: ls <caminho>      (lista arquivos de um diretório; use "." para a raiz)
ACTION: grep <termo>      (busca textual em todas as notas)
ACTION: read <arquivo>    (lê o conteúdo de uma nota)

Após cada ACTION você receberá o resultado. Você tem no máximo {max_actions}
ações no total — use-as bem.

Quando tiver o que precisa, produza os arquivos finais neste formato exato
(pode haver mais de um bloco FILE):

FILE: caminho/relativo/do/Arquivo.java
```java
<conteúdo completo do arquivo>
```

Regras do formato: nunca misture ACTION e FILE na mesma resposta; escreva
arquivos completos e compiláveis; não modifique os arquivos existentes do
projeto."""

SYSTEM_BASELINE = """Você é um engenheiro de software sênior de um time de produto.
Você NÃO tem acesso à documentação do time; use seu melhor julgamento para
regras de negócio e convenções.

Produza os arquivos finais neste formato exato (pode haver mais de um bloco
FILE):

FILE: caminho/relativo/do/Arquivo.java
```java
<conteúdo completo do arquivo>
```

Escreva arquivos completos e compiláveis; não modifique os arquivos
existentes do projeto."""


def log(msg):
    print(f"[{CASE}] {msg}", flush=True)


# ---------------------------------------------------------------- ollama ----

def chat(messages, stats):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {"num_ctx": NUM_CTX, "temperature": TEMPERATURE},
    }
    data = json.dumps(payload).encode()
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(
                f"{OLLAMA}/api/chat", data=data,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=900) as r:
                resp = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if attempt == 1 and "think" in body:
                payload.pop("think", None)
                data = json.dumps(payload).encode()
                continue
            raise RuntimeError(f"Ollama HTTP {e.code}: {body[:500]}")
    stats["prompt_tokens"] += resp.get("prompt_eval_count", 0)
    stats["completion_tokens"] += resp.get("eval_count", 0)
    content = resp.get("message", {}).get("content", "")
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.S).strip()
    return content


# ----------------------------------------------------------- vault tools ----

def safe_vault_path(rel):
    rel = rel.strip().strip('"').strip("'") or "."
    p = (VAULT / rel).resolve()
    root = VAULT.resolve()
    if p != root and root not in p.parents:
        raise ValueError("caminho fora da base de conhecimento")
    return p


def tool_ls(arg):
    p = safe_vault_path(arg)
    if not p.exists():
        return f"não existe: {arg}"
    if not p.is_dir():
        return f"não é um diretório: {arg}"
    entries = sorted(
        e.name + ("/" if e.is_dir() else "") for e in p.iterdir())
    return "\n".join(entries) or "(vazio)"


def tool_grep(term):
    term = term.strip().strip('"').strip("'")
    if not term:
        return "uso: ACTION: grep <termo>"
    hits = []
    for f in sorted(VAULT.rglob("*.md")):
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            if term.lower() in line.lower():
                hits.append(f"{f.relative_to(VAULT).as_posix()}:{n}: {line.strip()[:160]}")
    if not hits:
        return f"nenhum resultado para: {term}"
    out = hits[:40]
    if len(hits) > 40:
        out.append(f"... ({len(hits) - 40} resultados omitidos)")
    return "\n".join(out)


def tool_read(arg, notes_read):
    p = safe_vault_path(arg)
    if not p.exists() or not p.is_file():
        return f"arquivo não encontrado: {arg}"
    notes_read.add(p.resolve().relative_to(VAULT.resolve()).as_posix())
    content = p.read_text(encoding="utf-8")
    if len(content) > 8000:
        content = content[:8000] + "\n... (truncado)"
    return content


# ------------------------------------------------------------- workspace ----

def prepare_workspace(task):
    ws = WORK / task["id"]
    if ws.exists():
        shutil.rmtree(ws)
    src = SCAFFOLD / ("frontend" if task["type"] == "frontend" else "backend")
    shutil.copytree(src, ws)
    return ws


def write_generated_files(ws, blocks):
    written = []
    for rel, content in blocks:
        rel = rel.strip().replace("\\", "/").lstrip("/")
        dest = (ws / rel).resolve()
        if ws.resolve() not in dest.parents:
            log(f"  ! caminho suspeito ignorado: {rel}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        written.append(rel)
        log(f"  + {rel}")
    return written


# ------------------------------------------------------------------ eval ----

def eval_backend(task, ws):
    test_src = EVAL_DIR / task["id"] / task["eval_file"]
    dest = ws / "src/test/java/com/bench/evaltest" / test_src.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(test_src, dest)
    smoke = ws / "src/test/java/com/bench/SmokeTest.java"
    if smoke.exists():
        smoke.unlink()

    try:
        r = subprocess.run(
            ["mvn", "-B", "test"], cwd=ws,
            capture_output=True, text=True, timeout=1200)
    except subprocess.TimeoutExpired:
        return {"compiled": False, "passed": 0, "total": task["expected_tests"],
                "tests": [], "error": "timeout do maven"}

    reports = list((ws / "target/surefire-reports").glob("TEST-*.xml"))
    if not reports:
        tail = (r.stdout + r.stderr)[-3000:]
        return {"compiled": False, "passed": 0, "total": task["expected_tests"],
                "tests": [], "error": f"sem relatorio surefire (compilacao?)\n{tail}"}

    tests = []
    for rep in reports:
        root = ET.parse(rep).getroot()
        for tc in root.iter("testcase"):
            fail_node = tc.find("failure")
            if fail_node is None:
                fail_node = tc.find("error")
            entry = {"name": tc.get("name"), "passed": fail_node is None}
            if fail_node is not None:
                msg = (fail_node.get("message") or "") + "\n" + (fail_node.text or "")
                entry["failure"] = msg.strip()[:600]
            tests.append(entry)
    passed = sum(1 for t in tests if t["passed"])
    return {"compiled": True, "passed": passed, "total": len(tests),
            "tests": tests, "error": None}


def eval_frontend(task, ws):
    script = EVAL_DIR / task["id"] / task["eval_file"]
    try:
        r = subprocess.run(
            ["node", str(script), str(ws)],
            capture_output=True, text=True, timeout=300)
        data = json.loads(r.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return {"compiled": False, "passed": 0, "total": task["expected_tests"],
                "tests": [], "error": f"avaliacao frontend falhou: {e}"}
    tests = data["results"]
    passed = sum(1 for t in tests if t["passed"])
    compiled = any(t["passed"] for t in tests if "tsc" in t["name"])
    error = None if compiled else (data.get("tsc_output") or "tsc falhou")[-2500:]
    return {"compiled": compiled, "passed": passed, "total": len(tests),
            "tests": tests, "error": error}


# ------------------------------------------------------------- task loop ----

def build_prompt(task):
    prompt = (TASKS_DIR / task["prompt_file"]).read_text(encoding="utf-8")
    ref_name = ("scaffold-frontend-ref.md" if task["type"] == "frontend"
                else "scaffold-backend-ref.md")
    ref = (TASKS_DIR / ref_name).read_text(encoding="utf-8")
    return f"{prompt}\n\n{ref}"


def run_task(task):
    log(f"=== {task['id']} — {task['title']} ===")
    t0 = time.time()
    ws = prepare_workspace(task)

    stats = {"prompt_tokens": 0, "completion_tokens": 0}
    notes_read = set()
    actions = []
    system = (SYSTEM_BASELINE if CASE == "baseline"
              else SYSTEM_VAULT.format(max_actions=MAX_ACTIONS))
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": build_prompt(task)},
    ]

    blocks = []
    nudges = 0
    while True:
        content = chat(messages, stats)
        messages.append({"role": "assistant", "content": content})

        # exploracao tem prioridade: se ha ACTION com cota disponivel, executa
        # (modelos coder misturam ACTION e FILE na mesma resposta; FILE so e
        # final quando vem sem ACTION ou com a cota esgotada)
        m = ACTION_RE.search(content) if CASE != "baseline" else None
        if not (m and len(actions) < MAX_ACTIONS):
            found = FILE_RE.findall(content)
            if found:
                blocks = found
                break

        if m and len(actions) < MAX_ACTIONS:
            cmd, arg = m.group(1), m.group(2)
            actions.append(f"{cmd} {arg}".strip())
            log(f"  ACTION {len(actions)}/{MAX_ACTIONS}: {cmd} {arg}")
            try:
                if cmd == "ls":
                    result = tool_ls(arg)
                elif cmd == "grep":
                    result = tool_grep(arg)
                else:
                    result = tool_read(arg, notes_read)
            except ValueError as e:
                result = str(e)
            remaining = MAX_ACTIONS - len(actions)
            note = ""
            if FILE_RE.search(content):
                note = ("\n\n(Seus blocos FILE foram IGNORADOS porque vieram "
                        "junto com um ACTION. Termine a exploração e reenvie "
                        "todos os FILE completos sozinhos na resposta final.)")
            messages.append({"role": "user", "content":
                             f"RESULT ({remaining} ações restantes):\n{result}{note}"})
            continue

        nudges += 1
        if nudges > MAX_NUDGES:
            log("  ! modelo não produziu arquivos; desistindo")
            break
        if m and len(actions) >= MAX_ACTIONS:
            messages.append({"role": "user", "content":
                             "Limite de ações atingido. Produza AGORA os blocos "
                             "FILE finais com o código completo."})
        else:
            messages.append({"role": "user", "content":
                             "Formato inválido. Responda apenas com um ACTION "
                             "válido ou com blocos FILE no formato especificado."})

    written = write_generated_files(ws, blocks)

    def evaluate():
        log("  avaliando...")
        return (eval_frontend(task, ws) if task["type"] == "frontend"
                else eval_backend(task, ws))

    repairs = 0
    if written:
        ev = evaluate()
        # loop de reparo: devolve erros de compilacao/type-check ao modelo
        while not ev["compiled"] and repairs < MAX_REPAIRS:
            repairs += 1
            log(f"  reparo {repairs}/{MAX_REPAIRS} (não compilou)")
            err = (ev.get("error") or "erro desconhecido")[-2500:]
            messages.append({"role": "user", "content":
                             "A compilação/verificação do seu código falhou:\n\n"
                             f"```\n{err}\n```\n\n"
                             "Corrija e reenvie TODOS os blocos FILE, com o "
                             "conteúdo completo de cada arquivo."})
            content = chat(messages, stats)
            messages.append({"role": "assistant", "content": content})
            found = FILE_RE.findall(content)
            if not found:
                break
            new_written = write_generated_files(ws, found)
            if not new_written:
                break
            written = sorted(set(written) | set(new_written))
            ev = evaluate()
    else:
        ev = {"compiled": False, "passed": 0, "total": task["expected_tests"],
              "tests": [], "error": "modelo não produziu arquivos"}

    gold = set(task["gold_notes"].get(CASE, []))
    result = {
        "task": task["id"],
        "title": task["title"],
        "case": CASE,
        "model": MODEL,
        "score": round(ev["passed"] / ev["total"], 3) if ev["total"] else 0.0,
        "passed": ev["passed"],
        "total": ev["total"],
        "compiled": ev["compiled"],
        "repairs": repairs,
        "error": ev["error"],
        "tests": ev["tests"],
        "files_written": written,
        "retrieval": {
            "actions": actions,
            "notes_read": sorted(notes_read),
            "gold_notes": sorted(gold),
            "gold_hits": sorted(gold & notes_read),
            "gold_hit_rate": round(len(gold & notes_read) / len(gold), 3) if gold else None,
        },
        "tokens": stats,
        "duration_s": round(time.time() - t0, 1),
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{task['id']}.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    transcript = "\n\n---\n\n".join(
        f"## {m['role']}\n\n{m['content']}" for m in messages)
    (RESULTS / f"{task['id']}_transcript.md").write_text(
        transcript, encoding="utf-8")

    log(f"  score {ev['passed']}/{ev['total']}  compilou={ev['compiled']}  "
        f"{result['duration_s']}s")
    return result


# ----------------------------------------------------------------- smoke ----

def smoke():
    log("SMOKE: verificando ambiente...")
    with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=30) as r:
        tags = json.loads(r.read())
    models = [m["name"] for m in tags.get("models", [])]
    log(f"  ollama ok, modelos: {models}")
    if not any(m.startswith(MODEL) for m in models):
        log(f"  ! modelo {MODEL} NÃO encontrado no ollama")
        sys.exit(1)
    stats = {"prompt_tokens": 0, "completion_tokens": 0}
    out = chat([{"role": "user", "content": "Responda apenas: ok"}], stats)
    log(f"  chat ok: {out[:60]!r}")
    if CASE != "baseline":
        n = len(list(VAULT.rglob("*.md")))
        log(f"  vault {VAULT}: {n} notas")
        if n == 0:
            sys.exit(1)
    for tool in (["mvn", "-v"], ["node", "-v"]):
        v = subprocess.run(tool, capture_output=True, text=True).stdout.splitlines()[0]
        log(f"  {tool[0]}: {v}")
    log("SMOKE: tudo ok")


def main():
    if os.environ.get("SMOKE") == "1":
        smoke()
        return
    if CASE not in ("vault-a", "vault-b", "baseline"):
        sys.exit(f"CASE inválido: {CASE}")
    meta = json.loads((TASKS_DIR / "tasks.json").read_text(encoding="utf-8"))
    filt = os.environ.get("TASK_FILTER")
    tasks = [t for t in meta["tasks"]
             if not filt or t["id"] in filt.split(",")]
    log(f"caso={CASE} modelo={MODEL} tarefas={[t['id'] for t in tasks]}")
    results = []
    for t in tasks:
        try:
            results.append(run_task(t))
        except Exception:
            tb = traceback.format_exc()
            log(f"!! tarefa {t['id']} abortou:\n{tb}")
            RESULTS.mkdir(parents=True, exist_ok=True)
            crash = {
                "task": t["id"], "title": t["title"], "case": CASE,
                "model": MODEL, "score": 0.0, "passed": 0,
                "total": t["expected_tests"], "compiled": False,
                "repairs": 0, "error": f"runner abortou: {tb[-1500:]}",
                "tests": [], "files_written": [],
                "retrieval": {"actions": [], "notes_read": [],
                              "gold_notes": [], "gold_hits": [],
                              "gold_hit_rate": None},
                "tokens": {"prompt_tokens": 0, "completion_tokens": 0},
                "duration_s": 0,
            }
            (RESULTS / f"{t['id']}.json").write_text(
                json.dumps(crash, indent=2, ensure_ascii=False),
                encoding="utf-8")
            results.append(crash)
    total_passed = sum(r["passed"] for r in results)
    total = sum(r["total"] for r in results)
    log(f"===== TOTAL {CASE}: {total_passed}/{total} =====")


if __name__ == "__main__":
    main()
