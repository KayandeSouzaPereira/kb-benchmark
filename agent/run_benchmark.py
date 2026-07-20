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
import signal
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
# devmcp: avaliacao via Quarkus dev mode + continuous testing (Dev MCP);
# classic: mvn test frio a cada avaliacao
EVAL_MODE = os.environ.get("EVAL_MODE", "devmcp")
DEV_MCP_URL = "http://localhost:8080/q/dev-mcp"
NUM_CTX = 16384
TEMPERATURE = 0.2

FILE_RE = re.compile(r"FILE:\s*([^\n`]+?)\s*\n```[a-zA-Z]*\s*\n(.*?)```", re.S)
ACTION_RE = re.compile(r"^ACTION:\s*(ls|grep|read)\s*(.*)$", re.M)

SYSTEM_VAULT = """You are a senior software engineer on a product team.
The team keeps a knowledge base of Markdown files with the business rules and
conventions. You MUST consult it before writing code, because the
product-specific rules are not obvious.

To explore the knowledge base, reply with ONE single command line per message:

ACTION: ls <path>       (lists files in a directory; use "." for the root)
ACTION: grep <term>     (text search across all notes)
ACTION: read <file>     (reads the content of a note)

After each ACTION you will receive the result. You have at most {max_actions}
actions in total — use them well.

When you have what you need, produce the final files in this exact format
(there may be more than one FILE block):

FILE: relative/path/to/File.java
```java
<complete file content>
```

Format rules: never mix ACTION and FILE in the same reply; write complete,
compilable files; do not modify the project's existing files."""

SYSTEM_BASELINE = """You are a senior software engineer on a product team.
You do NOT have access to the team's documentation; use your best judgment for
business rules and conventions.

Produce the final files in this exact format (there may be more than one FILE
block):

FILE: relative/path/to/File.java
```java
<complete file content>
```

Write complete, compilable files; do not modify the project's existing
files."""


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


# --------------------------------------------------- dev mode (Dev MCP) -----

def _tail_file(path, n=3000):
    try:
        txt = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "(sem log)"
    txt = re.sub(r"\x1b\[[0-9;]*m", "", txt)
    return txt[-n:]


class DevMode:
    """Processo `mvn quarkus:dev` persistente por tarefa, dirigido via Dev MCP."""

    def __init__(self, ws):
        self.ws = ws
        self.log = ws / "devmode.log"
        self.proc = None
        self._logf = None
        self.ready = False
        self.last_run = 0
        self.boot_wait_s = None

    def start(self):
        # mata qualquer dev mode orfao de tarefa anterior (libera a porta 8080)
        subprocess.run(["pkill", "-f", "quarkus:dev"], capture_output=True)
        time.sleep(1)
        self._logf = open(self.log, "w", encoding="utf-8")
        self.proc = subprocess.Popen(
            ["mvn", "-B", "quarkus:dev", "-Dquarkus.analytics.disabled=true"],
            cwd=self.ws, stdout=self._logf, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, start_new_session=True)

    def _rpc(self, method, params=None, timeout=30):
        payload = {"jsonrpc": "2.0", "id": 1, "method": method}
        if params is not None:
            payload["params"] = params
        req = urllib.request.Request(
            DEV_MCP_URL, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                     "Accept": "application/json, text/event-stream"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())

    def tool(self, name):
        data = self._rpc("tools/call", {"name": name, "arguments": {}})
        txt = data.get("result", {}).get("content", [{}])[0].get("text", "")
        try:
            return json.loads(txt)
        except (json.JSONDecodeError, TypeError):
            return txt

    def wait_ready(self, timeout=120):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.proc.poll() is not None:
                raise RuntimeError(
                    f"quarkus:dev terminou (rc={self.proc.returncode}):\n"
                    + _tail_file(self.log))
            try:
                self._rpc("ping", timeout=5)
                return
            except (urllib.error.URLError, OSError, TimeoutError):
                time.sleep(2)
        raise RuntimeError("Dev MCP nao respondeu:\n" + _tail_file(self.log))

    def wait_new_run(self, timeout):
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                st = self.tool("devui-continuous-testing_getStatus")
            except (urllib.error.URLError, OSError, TimeoutError):
                st = None
            if (isinstance(st, dict) and st.get("lastRun", 0) > self.last_run
                    and st.get("running", -1) == -1):
                self.last_run = st["lastRun"]
                return st
            time.sleep(2)
        return None

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
                self.proc.wait(timeout=20)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
        if self._logf:
            self._logf.close()


def parse_ct_results(data):
    """Extrai testes por metodo do JSON do getTestResults (defensivo)."""
    found = {}

    def walk(o):
        if isinstance(o, dict):
            for key in ("passing", "failing", "skipped"):
                if isinstance(o.get(key), list):
                    for e in o[key]:
                        dn = e.get("displayName", "") if isinstance(e, dict) else ""
                        if "#" in dn:
                            name = dn.split("#", 1)[1].rstrip("()")
                            item = {"name": name,
                                    "passed": e.get("state") == "PASSED"}
                            thr = ((e.get("testExecutionResult") or {})
                                   .get("throwable") or {})
                            if thr.get("message"):
                                item["failure"] = thr["message"].strip()[:600]
                            found[name] = item
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    return list(found.values())


def eval_backend_devmcp(task, ws, dev):
    if not dev.ready:
        boot0 = time.time()
        if dev.proc is None or dev.proc.poll() is not None:
            dev.start()
        try:
            # fonte quebrada impede o dev mode de subir o HTTP; o processo
            # fica re-tentando compilar — tratamos como falha de compilacao
            # reparavel e o proximo evaluate() tenta de novo
            dev.wait_ready()
        except RuntimeError as e:
            return {"compiled": False, "passed": 0,
                    "total": task["expected_tests"], "tests": [],
                    "error": f"dev mode nao subiu (compilacao?):\n{e}"[-3500:]}
        dev.tool("devui-continuous-testing_start")
        dev.ready = True
        dev.boot_wait_s = round(time.time() - boot0, 1)
        st = dev.wait_new_run(180)
    else:
        # run incremental disparado pela escrita dos arquivos (pode nao vir)
        st = dev.wait_new_run(60)

    # forca um run COMPLETO: os contadores por-run do getStatus enganam em
    # runs incrementais (re-rodam so os afetados); o placar vem do estado
    # cumulativo do getTestResults apos um runAll
    try:
        dev.tool("devui-continuous-testing_runAll")
        st2 = dev.wait_new_run(90)
    except (urllib.error.URLError, OSError, TimeoutError):
        st2 = None
    if st2 is not None:
        st = st2
    if st is None:
        return {"compiled": False, "passed": 0,
                "total": task["expected_tests"], "tests": [],
                "error": "continuous testing nao produziu novo run "
                         "(erro de compilacao?)\n" + _tail_file(dev.log)}

    try:
        detail = dev.tool("devui-continuous-testing_getTestResults")
        tests = parse_ct_results(detail)
    except (urllib.error.URLError, OSError, TimeoutError):
        tests = []
    total = task["expected_tests"]
    if tests:
        passed = sum(1 for t in tests if t["passed"])
    else:
        passed = int(st.get("totalTestsPassed", 0))
    passed = min(passed, total)
    return {"compiled": True, "passed": passed, "total": total,
            "tests": tests, "error": None}


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

    dev = None
    if task["type"] == "backend" and EVAL_MODE == "devmcp":
        test_src = EVAL_DIR / task["id"] / task["eval_file"]
        dest = ws / "src/test/java/com/bench/evaltest" / test_src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(test_src, dest)
        smoke = ws / "src/test/java/com/bench/SmokeTest.java"
        if smoke.exists():
            smoke.unlink()
        dev = DevMode(ws)
        dev.start()
        log("  quarkus:dev subindo em paralelo com a geração")

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
                note = ("\n\n(Your FILE blocks were IGNORED because they came "
                        "together with an ACTION. Finish exploring and resend "
                        "ALL complete FILE blocks alone in your final reply.)")
            messages.append({"role": "user", "content":
                             f"RESULT ({remaining} actions left):\n{result}{note}"})
            continue

        nudges += 1
        if nudges > MAX_NUDGES:
            log("  ! modelo não produziu arquivos; desistindo")
            break
        if m and len(actions) >= MAX_ACTIONS:
            messages.append({"role": "user", "content":
                             "Action limit reached. Produce the final FILE "
                             "blocks with the complete code NOW."})
        else:
            messages.append({"role": "user", "content":
                             "Invalid format. Reply only with a valid ACTION "
                             "or with FILE blocks in the specified format."})

    written = write_generated_files(ws, blocks)

    eval_times = []

    def evaluate():
        log("  avaliando...")
        e0 = time.time()
        if task["type"] == "frontend":
            ev = eval_frontend(task, ws)
        elif dev is not None:
            ev = eval_backend_devmcp(task, ws, dev)
        else:
            ev = eval_backend(task, ws)
        eval_times.append(round(time.time() - e0, 1))
        log(f"  avaliação em {eval_times[-1]}s")
        return ev

    repairs = 0
    if written:
        ev = evaluate()
        # loop de reparo: devolve erros de compilacao/type-check ao modelo
        while not ev["compiled"] and repairs < MAX_REPAIRS:
            repairs += 1
            log(f"  reparo {repairs}/{MAX_REPAIRS} (não compilou)")
            err = (ev.get("error") or "erro desconhecido")[-2500:]
            messages.append({"role": "user", "content":
                             "Compilation/verification of your code failed:\n\n"
                             f"```\n{err}\n```\n\n"
                             "Fix it and resend ALL FILE blocks with the "
                             "complete content of each file."})
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

    if dev is not None:
        dev.stop()

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
        "eval_mode": ("frontend" if task["type"] == "frontend"
                      else ("devmcp" if dev is not None else "classic")),
        "eval_times_s": eval_times,
        "dev_boot_wait_s": dev.boot_wait_s if dev is not None else None,
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
