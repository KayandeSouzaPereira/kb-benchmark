# Final report — Knowledge Base benchmark for coding agents

**Date:** 2026-07-19 to 2026-07-20 · **Author:** automated benchmark (Claude Code + local Ollama)
**Location:** `C:\dev\kb-benchmark` · **Raw data:** `results/` (v7), `results-v2/`, `results-v3/`, `results-v4-invalid/`, `results-v5/`, `results-v6/`, `results-v7-runs/` (11-round statistical confirmation)

*(This is an English translation of [RELATORIO.md](RELATORIO.md), the original Portuguese report. Both are kept in sync; if they ever diverge, RELATORIO.md is the source of truth.)*

---

## 1. Question

Which knowledge base organization (Obsidian/Markdown) best serves as a context
source for a **local coding agent**?

| Condition | Service | Description |
|---|---|---|
| **A — Vault structured for agents** | `bench-a` | Semantic folders (`domain/`, `decisions/`, `code-standards/`…), a routing `INDEX.md`, kebab-case names, YAML frontmatter, standardized sections ("When to use / Anti-patterns / Discarded alternatives") |
| **B — Classic Zettelkasten** | `bench-b` | Atomic notes with timestamp IDs, single flat folder, dense wikilinks, structure notes, "thinking in progress" notes including a contradictory pair with a later correction |
| **C — Baseline** | `bench-c` | No knowledge base |

The rule **content** is identical in A and B — only organization, granularity
and navigation mechanism differ.

## 2. Method

- **Domain:** multi-tenant user-management SaaS. Rules are deliberately
  non-guessable: invitations expire in 72h, max 3 resends, a pending
  invitation counts toward the plan limit (FREE=5), soft-delete with a 30-day
  purge, self-deletion forbidden, OWNER protections (`OWNER_PROTECTED`,
  `LAST_OWNER`), a `{code, message}` error envelope with stable codes,
  mandatory auditing with an action enum, status badges with canonical CSS
  classes and pt-BR labels.
- **Tasks:** 5 (4 backend Quarkus 3/Java 21, 1 frontend Angular 18), graded by
  **31 automated black-box tests** (JUnit 5 + RestAssured; tsc + static checks
  on the frontend). Tasks state *what* to build; the rules exist only in the KB.
- **Agent:** an agentic loop over a text protocol — `ACTION: ls|grep|read`
  (max. 8 steps) against the vault mounted in the container, then `FILE:`
  blocks with the code. Up to 3 repair rounds fed with compilation errors
  (javac/tsc).
- **Infra:** one isolated Docker container per condition (JDK 21 + Maven +
  Node 20); the model is served by Ollama on the **host** (RTX 2060 Super
  8 GB GPU) via `host.docker.internal:11434` — same model, same quantization
  for all 3 cases.
- **Metrics:** tests passed, compilation, number of repairs, retrieval
  actions, notes read, "gold-note" hit rate (the notes that contain the
  task's rules), tokens, duration. Full per-task transcripts in
  `results/<case>/tN_transcript.md`.

## 3. Rounds run

| Round | Model | Change | A | B | C |
|---|---|---|---|---|---|
| v2 | qwen3:8b | 2 compilation repair rounds | 7/31 | 7/31 | 3/31 |
| v3 | qwen3:8b | 3 repairs + neutral Java API hints | 8/31 | 8/31 | 2/31 |
| v4 | qwen3-coder:30b | *discarded* — scaffold bug (see §6) | — | — | — |
| v5 | qwen3-coder:30b | fixed scaffold (`@Singleton`) | 11/31 (35%) | 12/31 (39%) | 4/31 (13%) |
| v6 | qwen3-coder:30b | evaluation via **Quarkus Dev MCP** (Quarkus 3.33 LTS) | 12/31 (39%) | 13/31 (42%) | 2/31 (6%) |
| v7 (single run) | qwen3-coder:30b | **KB and prompts translated to English** + `@HeaderParam` hint | 21/31 (68%) | 15/31 (48%) | 8/31 (26%) |
| **v7 (11-round confirmation, definitive)** | **qwen3-coder:30b** | same v7 config, run 11 independent times | **23.3 ± 1.9/31** | **18.8 ± 3.4/31** | **7.5 ± 0.8/31** |

### v7: English + header hint — the benchmark's biggest jump

| Task | A | B | C |
|---|---|---|---|
| t1 — Create invitation | **4/6** | **4/6** | 1/6 |
| t2 — Delete user | **4/7** | 3/7 | 2/7 |
| t3 — Resend invitation | **5/5** | 0/5 † | 0/5 |
| t4 — Change role | **6/6** | **6/6** | 3/6 |
| t5 — Angular badges | 2/7 | 2/7 | 2/7 |

† The B vault read both gold notes for the resend rule (perfect retrieval),
but declared `@Consumes(APPLICATION_JSON)` on a body-less POST → 415 on every
test. Without that single API slip, A and B would have tied at 20/31.

v7 changes and attribution of the gains:

- **Everything translated to English** (both content AND file names in the
  vaults, task prompts, agent prompts). Badge labels stay pt-BR as an
  explicit product rule ("do not translate").
- **Neutral `@HeaderParam` hint** with a signature example in the reference
  scaffold — unlocked t4 in all 3 cases (0→3/6/6): it had been the wrong
  stub/`@Context` usage zeroing the task since v5.
- Discounting the hint's effect (t4), **language accounts for the rest of the
  jump**: t1 0→4, t2 1-2→3-4 in the KB cases, and the structured vault's
  retrieval jumped from 27% to **67% gold-note hit rate** — English file
  names are navigated much better by the model. Tokens per task dropped ~30%
  (English is denser) and average backend task duration fell along with it.
- First round where A > B on the scoreboard (21 vs 15), but the gap was
  almost entirely the t3 accident (†) — the honest verdict at the time was
  still "technical tie with different profiles," now with A navigating as
  well as B (gold-hit 0.67 × 0.67) while spending less.

### v6 per-task detail

| Task | A | B | C |
|---|---|---|---|
| t1 — Create invitation | **3/6** | 1/6 | 0/6 |
| t2 — Delete user (soft-delete) | 2/7 | 1/7 | 0/7 |
| t3 — Resend invitation | **5/5** | **5/5** | 0/5 |
| t4 — Change role | 0/6 * | 0/6 * | 0/6 * |
| t5 — Angular badges | 2/7 | **6/7** | 2/7 |

### v6: evaluation via Quarkus Dev MCP (the infra change)

Starting with v6, backend evaluation stopped running `mvn test` cold (a fresh
JVM every round, 30–90 s) and switched to a **persistent `mvn quarkus:dev`
per task**, driven by **Dev MCP** (`/q/dev-mcp`, Quarkus 3.33): the runner
calls the `devui-continuous-testing_start/runAll/getStatus/getTestResults`
tools over JSON-RPC and scores from the cumulative per-test state. Dev mode
boots **in parallel with the model's generation**.

Measured result (12 backend tasks, same conditions):

| Metric | v5 (cold mvn test) | v6 (Dev MCP) |
|---|---|---|
| Average duration per backend task | 195 s | **104 s (−47%)** |
| Evaluation per round | 30–90 s | **~17 s** (includes a safety `runAll`) |
| Effective boot wait | — | **2.2 s** (overlapped with generation) |
| Re-run after a code change | new JVM | **~3 s** (hot reload) |
| Compilation error feedback | only via a full run | near-instant, in the dev mode log |

Two Dev MCP traps were discovered (and handled) along the way — see §6.

\* t4 zeroed out in all 3 cases due to the same model vice: instead of
reading the `X-Actor-Id` header, it generated
`return "actor-id"; // Placeholder for demonstration` — every request fell
into 404. A model failure, identical across the three conditions (does not
bias the comparison).

### Retrieval and cost (v6)

| Metric | A — structured | B — Zettelkasten | C — no KB |
|---|---|---|---|
| Retrieval actions (avg/task) | 6.4 | 6.8 | 0 |
| Notes read (avg) | 1.8 | 5.2 | 0 |
| **Gold-note hit rate** | **0.27** | **0.93** | — |
| Prompt tokens (avg) | 14,033 | 18,458 | 721 |
| Duration per task (avg) | 123 s | 133 s | 63 s |

The retrieval pattern replicated across **4 rounds**: B finds the right notes
~87–93% of the time, A ~27–47%; B reads 2–3× more notes and costs ~30–40%
more tokens. In v6, A's shallow exploration was even more evident (1.8 notes
per task), and the score still tied — the model compensates part of what it
didn't read with common sense, but loses exactly the non-guessable rules.

## 3.5. Statistical confirmation — 11 independent rounds (v7)

A single round cannot separate a real effect from sampling luck — a 30B
coder-model has meaningful sampling variance. To confirm the v7 numbers, I
ran **10 additional independent rounds** with the exact same configuration
(qwen3-coder:30b, English KB, Dev MCP evaluation, `@HeaderParam` hint), added
to the already-published round (`round-00`) — 11 data points total. Raw data
in `results-v7-runs/`, full aggregation in
[`results-v7-runs/AGGREGATE.md`](results-v7-runs/AGGREGATE.md).

### Total score per round (31 tests)

| Round | C — No KB | A — Structured vault | B — Zettelkasten |
|---|---|---|---|
| round-00 | 8 | 21 | 15 |
| round-01 | 8 | 21 | 17 |
| round-02 | 8 | 23 | 25 |
| round-03 | 8 | 23 | 16 |
| round-04 | 6 | 26 | 15 |
| round-05 | 8 | 23 | 20 |
| round-06 | 6 | 26 | 18 |
| round-07 | 8 | 21 | 22 |
| round-08 | 7 | 26 | 15 |
| round-09 | 8 | 23 | 21 |
| round-10 | 8 | 23 | 23 |
| **Mean ± stdev** | **7.5 ± 0.8** | **23.3 ± 1.9** | **18.8 ± 3.4** |
| **Min–Max** | 6–8 | 21–26 | 15–25 |

### What the larger sample confirms and corrects

1. **The KB effect is beyond question.** Across 11 independent rounds, the
   baseline's range (6–8) and the weaker vault's range (15–25 for B, 21–26
   for A) **never overlap**. It's not one-round luck — it's a ~3× effect
   that repeats every single time.

2. **The structured vault (A) is consistently better than the Zettelkasten
   (B) — this corrects the "technical tie" conclusion from the original v7
   run.** With just one round, A=21 and B=15 looked like noise; across 11,
   A never dropped below 21 and B never exceeded 25, with means of 23.3 vs
   18.8 (a +4.5-point difference, effect size ≈1.6 pooled standard
   deviations — large by the usual statistical convention). B has nearly
   twice A's standard deviation (3.4 vs 1.9): A isn't just better, it's more
   **predictable**.

3. **A's advantage is not retrieval — both find the right notes almost
   equally well** (mean gold-hit: A 0.69, B 0.68, nearly identical across
   the 11 rounds). The difference lies downstream, in generating code from
   what was read.

4. **The per-task pattern is stable and reveals a real division of
   strengths:**

   | Task | A (mean±sd) | B (mean±sd) | Winner |
   |---|---|---|---|
   | t1 — Create invitation | 5.5±0.9/6 | 4.3±1.1/6 | **A**, by a wide margin |
   | t2 — Delete user | 6.7±0.9/7 | 3.9±0.3/7 | **A**, by a wide margin |
   | t3 — Resend invitation | **5.0±0.0/5** | 2.7±2.5/5 | **A**, with zero variance |
   | t4 — Change role | 4.1±1.4/6 | **5.5±1.7/6** | **B** |
   | t5 — Angular badges | 2.0±0.0/7 | 2.5±1.4/7 | B, slightly |

5. **Extra finding: vault-b's t3 is literally bimodal — 0/5 or 5/5, never
   partial** (6 rounds at 5/5, 5 at 0/5). Investigated: in **100% of
   rounds** the model read both correct gold notes for the resend rule. The
   cause is a code-generation coin-flip — in some rounds the model annotates
   the resend `@Path` with a class-inherited `@Consumes(APPLICATION_JSON)`,
   which rejects the body-less resend `POST` with `415`. It's not a
   knowledge failure; it's a JAX-RS syntax inconsistency specific to that
   endpoint shape. This alone explains B's huge t3 standard deviation (2.5)
   against A's zero.

6. **Vault A's t5 (Angular) is suspiciously flat**: exactly 2/7 in **all 11
   rounds**, zero variance — a hint of a systematic ceiling (probably the
   same incomplete-response pattern seen in v5/vault-b, now consistently
   reproduced on the A side) rather than a statistical coincidence.

### Revised verdict

The "technical tie A≈B" conclusion from earlier rounds **does not hold** with
11 samples: **A wins comfortably and more consistently** in the aggregate,
largely thanks to two strong points (t2, t3) where A is nearly perfect and B
suffers from a reproducible syntax bug. B still clearly wins t4 and slightly
wins t5. In other words: KB organization is not neutral for this model — the
structured vault with an `INDEX.md` produces better and more stable results
on most tasks in this benchmark, even with a gold-note hit rate equivalent to
the Zettelkasten's.

## 4. Conclusions

0. **KB language matters — a lot.** Translating the vaults (content and file
   names), task prompts and agent prompts from pt-BR to English took the
   benchmark from 12-13/31 to 15-21/31 in the KB cases (and the baseline from
   2 to 8, combined with the header hint). The sharpest effect was on
   filesystem retrieval: with English file names, the structured vault's
   gold-note hit rate jumped from 27% to 67% — the model navigates file
   names semantically, and Portuguese names were an invisible source of
   friction. For KBs consumed by agents, write in English (keeping product
   strings in the product's language, as an explicit rule).

1. **Evaluating with Quarkus Dev MCP works and pays for itself.** v6 proved
   that continuous testing can be driven over MCP inside an automated
   harness: −47% time per backend task, near-instant compilation feedback
   for the repair loop, and richer per-test detail than surefire (failure
   message + HTTP request/response). Recommended as the harness default from
   here on (`EVAL_MODE=devmcp`; `classic` kept as a fallback).

2. **Having a KB ≈ 2–6× the result — in every round, with two different
   models.** The textbook case is t3: one well-written atomic note about
   invitation resends produced **5/5 in both vaults against 0/5 for the
   baseline** — a perfect transfer of a business rule into code. The
   baseline never gets right what cannot be guessed (72h, error codes,
   30-day retention).

3. **Zettelkasten vs. structured vault: looked like a tie with 1 round; with
   11 independent rounds (§3.5), the structured vault wins comfortably and
   more consistently.**
   - **A (structured)** won 3 of 5 tasks by large margins (t1, t2, t3) and
     with a much lower total standard deviation (1.9 vs 3.4) — it's the more
     predictable option.
   - **B (Zettelkasten)** won t4 and slightly t5, but with twice A's
     variance — including a bimodal case in t3 (0/5 or 5/5, never partial)
     caused by a reproducible JAX-RS annotation bug, not a knowledge
     failure.
   - The difference **is not retrieval**: both find the right gold notes
     almost equally well (gold-hit ~0.68–0.69 across the 11 rounds). A's
     advantage is entirely downstream, in translating "read the right rule"
     into "generated correct code on the first try."

4. **The bottleneck is the model, not the organization.** qwen3:8b died on
   Java syntax (72% of KB tasks failed to compile); coder:30b compiles
   everything but commits sins of spec adherence (a placeholder instead of
   the header, an invented audit action). With local models in this class,
   the KB improves the result a lot, but does not close the gap to
   "production."

### Practical recommendation (revised after the 11-round confirmation)

This report's original recommendation was an "A+B hybrid" — A's folders +
INDEX combined with the Zettelkasten's dense-linking discipline. The 11-round
data (§3.5) **does not support that recommendation**: the premise was that A
needed to "borrow" B's mechanism because it retrieved worse (true in v6,
where A's gold-hit was 0.27); but that was already untrue by the single v7
run (0.67×0.67), and the 11-round confirmation settles it (0.69×0.68,
essentially identical). Without that retrieval gap to justify borrowing, the
formal hybrid loses its rationale — and A already beats B comfortably, with
twice the consistency.

**Current recommendation: use method A as the default** — semantic folders +
a routing `INDEX.md` + frontmatter + a "Related" section with relative links
at the end of each note (vault A already includes this; it's the most useful
part of the Zettelkasten's graph mechanism, without needing timestamp IDs or
abandoning the folder hierarchy). Pure Zettelkasten (B) remains a defensible
choice only in a specific scenario this benchmark **did not test**: a KB
large enough that a hand-maintained index stops being practical and
link-following becomes the only viable way to find the right rule. That
experiment was built and run — see §4.5.

## 4.5. v8 — Extended KB (~65 notes) and a multi-hop task

**Design**: both vaults were extended in place from ~15 to ~63–73 notes
each, with 5 new sub-areas (`billing/`, `webhooks/`, `notifications/`,
`rate-limiting/`, `sso/` — the last one is pure noise, no task uses notes
from there). New task **t6**: an internal payment-failure endpoint whose
correct implementation requires synthesizing **6 gold notes spread across 4
sub-areas** (HMAC-SHA256 webhook signing, retry policy, a 10-delivery/60-min
rolling-window rate limit, notification template, tenant digest mode) — no
single one is sufficient on its own. `MAX_ACTIONS` went from 8 to 14 to give
an exploration budget matching the new KB size.

Along the way, two real harness bugs were found and fixed during sanity
testing (not model-behavior findings): the `ls/grep/read` tool error
messages were still in Portuguese (a leftover from before the v7 English
translation — contaminating a harness that was supposed to be 100% English),
and `grep` couldn't parse realistic invocations like `grep -r "term" .` (the
parser treated everything, flags included, as the literal search term,
always returning zero results). Before the fix, vault-a scored 1/6 on t6
(it burned its whole budget guessing wrong file names); after the fix, it
rose to 4/6, correctly reading all 6 gold notes.

### Result (single run, qwen3-coder:30b)

| Task | A — Structured vault | B — Zettelkasten | C — No KB |
|---|---|---|---|
| t1 | 1/6 | 3/6 | 1/6 |
| t2 | **7/7** | **7/7** | 2/7 |
| t3 | **5/5** | **5/5** | 0/5 |
| t4 | **6/6** | **6/6** | 3/6 |
| t5 | **7/7** | **7/7** | 2/7 |
| t6 (new, multi-hop) | 4/6 | 4/6 | 2/6 |
| **Total** | **30/37 (81%)** | **32/37 (86%)** | **10/37 (27%)** |

| Metric | A | B | C |
|---|---|---|---|
| Notes read (avg) | 5.83 | 9.83 | 0 |
| **Gold-note hit rate** | **1.00** | **0.94** | — |
| Prompt tokens (avg) | 33,627 | 72,628 | 1,023 |
| Duration per task (avg) | 83 s | 407 s | 77 s |

### What this says about the giant-KB hypothesis

**The direct answer to the question that motivated this experiment —
"does the Zettelkasten win once a hand-maintained index stops scaling?" —
is no, at least not at ~65 notes with this model.** On t6, the task
purpose-built to stress multi-hop navigation in a large KB, **both
conditions hit 100% and 94% gold-hit and tied exactly at 4/6** — including
failing the exact same two checks
(`sendsImmediateNotificationWithCorrectTemplateByDefault`,
`queuesNotificationWhenTenantPrefersDailyDigest`). Digging in: both cases
read all 6 gold notes correctly but **neither created the
`NotificationLog`** — not a knowledge gap, but the model dropping the task's
3rd requirement (notify) after implementing the first two (sign the
webhook, apply the rate limit). An identical execution failure in both
conditions, not a KB-organization issue.

Further: vault A's `INDEX.md` **kept working well at 65 notes** —
gold-hit of 1.00, the best of the entire series. The prediction that a
hand-maintained index "stops scaling" did not hold at this size; it may
take a much larger KB (200+ notes) for the effect to show, or it may simply
not show up at all with a well-written `INDEX.md` plus a "Related" section
per note.

The cost pattern held and got more extreme: B read almost twice as many
notes (9.83 vs 5.83) and spent **more than double the tokens** (72,628 vs
33,627) for accuracy statistically indistinguishable from A's. In one case
(vault-b, t1) the accumulated conversation history reached **191,000
cumulative tokens** across 13 actions + 1 repair, and the task took 33
minutes — 15–20× normal. This is a direct side effect of raising
`MAX_ACTIONS`: more exploration budget helps find the right note, but if the
model uses the whole budget, latency cost explodes because the protocol
resends the full history on every action (~quadratic growth). Worth taming
in a future round (summarizing old reads, or separating exploration from
generation).

> ⚠️ **Pending validation**: this cost/latency spike was observed in a single
> task, in a single run. We don't yet know whether it's a systematic pattern
> (e.g., it happens whenever the model uses close to the max action budget)
> or a one-off outlier from this specific execution. **Before acting on it**
> (touching `MAX_ACTIONS`, changing the history protocol, etc.), rerun v8 a
> few more times — the same way the v7 11-round confirmation was done
> (§3.5) — to confirm whether the problem recurs and how often. Investigation
> already flagged as a separate task (`task_445c5d96`).

**Important caveat**: this is a single run — vault A's t1 dropped to 1/6
despite perfect gold-hit (the failure was in code generation, not
retrieval), exactly the kind of sampling noise the v7 11-round confirmation
showed to be normal for this model. "A ≈ B even at large KB scale" cannot be
promoted to a statistical conclusion without repeating v8 multiple times —
a natural next step.

## 5. Answers to the original questions

- **"Can local qwen 3 generate code inside a Docker environment?"** Yes.
  Validated architecture: Ollama on the host (GPU) + containers as isolated
  clients (workspace/KB/toolchain per condition). With 8 GB of VRAM you
  can't run 3 model instances; sharing the host's model is also the more
  scientifically fair design.
- **"Zettelkasten or by-topic?"** With 11 confirmed rounds (§3.5), by-topic
  (A) wins comfortably and twice as consistently. We also tested whether the
  Zettelkasten would turn the tables once the KB gets too large for a
  hand-maintained index (§4.5): it didn't, at least at ~65 notes — A and B
  tied exactly on the multi-hop task, with A spending less than half the
  tokens. Recommendation: use by-topic (A) as the default.

## 6. Engineering findings along the way

- **Quarkus client proxy (cause of the discarded v4):** an
  `@ApplicationScoped` bean with public fields → field access reads the
  *proxy*, while a method call delegates to the real instance — two distinct
  states in the "same" object. Tests seeded via the field, the model's code
  read via a method → 401 on everything. Fix: `@jakarta.inject.Singleton`
  (no proxy). Lesson: never mix public-field state with proxied beans.
- **`Response.Status.UNPROCESSABLE_ENTITY` does not exist** in JAX-RS — the
  KB taught 422 and the model tripped on the API; whoever *didn't* read the
  KB compiled by attempting less. Mitigated with a neutral technology hint
  in the reference scaffold (v3+).
- **`shutil.copytree` breaks `node_modules/.bin` shims** — `npx tsc` dies in
  a copied workspace; use `node node_modules/typescript/lib/tsc.js` instead.
- **Coder-models mix exploration and the final answer** — the protocol needs
  to prioritize exploration when ACTION and FILE arrive together, or the
  agent "answers" without ever reading the KB.
- **Dev MCP: per-run counters are misleading.** `getStatus.testsPassed`
  counts only the incremental run (continuous testing re-runs only the
  affected tests) — an incremental run can report 0 passed with everything
  green. The correct score comes from the cumulative state of
  `getTestResults` after an explicit `runAll`.
- **Dev MCP: a broken source at boot = a mute endpoint.** If the code
  doesn't compile when `quarkus:dev` comes up, the HTTP endpoint (and
  `/q/dev-mcp`) never opens — but the process keeps retrying to compile. The
  harness needs to treat a boot timeout as a repairable compilation error
  (dev mode boots on its own once the model fixes the file).

## 7. Reproduce

```powershell
# prerequisites: Docker Desktop + Ollama on the host with the desired model
docker compose build
docker compose run --rm bench-c   # baseline
docker compose run --rm bench-a   # structured vault
docker compose run --rm bench-b   # zettelkasten
python agent/report.py            # generates results/report.md

# for the 11-round statistical confirmation:
python agent/aggregate_rounds.py results-v7-runs

# variables: MODEL=qwen3:8b|qwen3-coder:30b  TASK_FILTER=t1,t3  SMOKE=1
#            EVAL_MODE=devmcp (default, Quarkus Dev MCP) | classic (cold mvn test)
```

Structure: `knowledge/` (both vaults), `tasks/` (prompts + scaffold
reference), `scaffold/` (Quarkus + Angular), `eval/` (31 tests), `agent/`
(agentic runner + report generator + round aggregator).
