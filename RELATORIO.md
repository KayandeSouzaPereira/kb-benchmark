# Relatório final — Benchmark de Knowledge Base para agentes de código

**Data:** 2026-07-19 · **Autor:** benchmark automatizado (Claude Code + Ollama local)
**Local:** `C:\dev\kb-benchmark` · **Dados brutos:** `results/` (v5), `results-v2/`, `results-v3/`, `results-v4-invalid/`

---

## 1. Pergunta

Qual organização de knowledge base (Obsidian/Markdown) serve melhor como fonte de
contexto para um **agente de código local**?

| Condição | Serviço | Descrição |
|---|---|---|
| **A — Vault estruturado p/ agentes** | `bench-a` | Pastas semânticas (`dominio/`, `decisoes/`, `padroes-codigo/`…), `INDEX.md` roteador, nomes kebab-case, frontmatter YAML, seções padronizadas ("Quando usar / Anti-padrões / Alternativas descartadas") |
| **B — Zettelkasten clássico** | `bench-b` | Notas atômicas com ID timestamp, pasta única, wikilinks densos, structure notes, notas de "pensamento em progresso" incluindo par contraditório com correção posterior |
| **C — Baseline** | `bench-c` | Sem knowledge base |

O **conteúdo** de regras é idêntico em A e B — muda apenas organização, granularidade
e mecanismo de navegação.

## 2. Método

- **Domínio:** SaaS multi-tenant de gestão de usuários. Regras propositalmente
  não-adivinháveis: convite expira em 72h, máx. 3 reenvios, convite pendente conta
  no limite do plano (FREE=5), soft-delete com purge em 30 dias, proibição de
  auto-exclusão, proteções de OWNER (`OWNER_PROTECTED`, `LAST_OWNER`), envelope de
  erro `{code, message}` com códigos estáveis, auditoria obrigatória com enum de
  ações, badges de status com classes CSS e rótulos PT-BR canônicos.
- **Tarefas:** 5 (4 backend Quarkus 3/Java 21, 1 frontend Angular 18), avaliadas por
  **31 testes automatizados** black-box (JUnit 5 + RestAssured; tsc + verificações
  estáticas no front). As tarefas dizem *o que* construir; as regras só existem na KB.
- **Agente:** loop agentic por protocolo de texto — `ACTION: ls|grep|read` (máx. 8
  passos) sobre a vault montada no container, depois blocos `FILE:` com o código.
  Até 3 rodadas de reparo alimentadas com os erros de compilação (javac/tsc).
- **Infra:** 1 container Docker isolado por condição (JDK 21 + Maven + Node 20);
  modelo servido pelo Ollama no **host** (GPU RTX 2060 Super 8 GB) via
  `host.docker.internal:11434` — mesmo modelo, mesma quantização para os 3 casos.
- **Métricas:** testes aprovados, compilação, nº de reparos, ações de retrieval,
  notas lidas, acerto de "notas-ouro" (as que contêm as regras da tarefa), tokens,
  duração. Transcripts completos por tarefa em `results/<caso>/tN_transcript.md`.

## 3. Rodadas executadas

| Rodada | Modelo | Mudança | A | B | C |
|---|---|---|---|---|---|
| v2 | qwen3:8b | 2 reparos de compilação | 7/31 | 7/31 | 3/31 |
| v3 | qwen3:8b | 3 reparos + dicas neutras de API Java | 8/31 | 8/31 | 2/31 |
| v4 | qwen3-coder:30b | *descartada* — bug de scaffold (ver §6) | — | — | — |
| v5 | qwen3-coder:30b | scaffold corrigido (`@Singleton`) | 11/31 (35%) | 12/31 (39%) | 4/31 (13%) |
| **v6 (definitiva)** | **qwen3-coder:30b** | avaliação via **Quarkus Dev MCP** (Quarkus 3.33 LTS) | **12/31 (39%)** | **13/31 (42%)** | **2/31 (6%)** |

### Detalhe v6 por tarefa

| Tarefa | A | B | C |
|---|---|---|---|
| t1 — Criar convite | **3/6** | 1/6 | 0/6 |
| t2 — Excluir usuário (soft-delete) | 2/7 | 1/7 | 0/7 |
| t3 — Reenviar convite | **5/5** | **5/5** | 0/5 |
| t4 — Alterar papel | 0/6 * | 0/6 * | 0/6 * |
| t5 — Badges Angular | 2/7 | **6/7** | 2/7 |

### v6: avaliação via Quarkus Dev MCP (a mudança de infra)

A partir da v6, a avaliação backend deixou de rodar `mvn test` frio (JVM nova a
cada rodada, 30–90 s) e passou a usar **`mvn quarkus:dev` persistente por
tarefa**, dirigido pelo **Dev MCP** (`/q/dev-mcp`, Quarkus 3.33): o runner chama
as tools `devui-continuous-testing_start/runAll/getStatus/getTestResults` via
JSON-RPC e pontua pelo estado cumulativo por teste. O dev mode sobe **em
paralelo com a geração do modelo**.

Resultado medido (12 tarefas backend, mesmas condições):

| Métrica | v5 (mvn test frio) | v6 (Dev MCP) |
|---|---|---|
| Duração média por tarefa backend | 195 s | **104 s (−47%)** |
| Avaliação por rodada | 30–90 s | **~17 s** (inclui `runAll` de segurança) |
| Espera efetiva de boot | — | **2,2 s** (sobreposto à geração) |
| Re-run após mudança de código | novo JVM | **~3 s** (hot reload) |
| Feedback de erro de compilação | só via run completo | quase instantâneo, no log do dev mode |

Duas armadilhas do Dev MCP descobertas (e tratadas) no caminho — ver §6.

\* t4 zerou nos 3 casos pelo mesmo vício do modelo: em vez de ler o header
`X-Actor-Id`, gerou `return "actor-id"; // Placeholder para demonstração` — todo
request caía em 404. Falha do modelo, idêntica nas três condições (não enviesa a
comparação).

### Retrieval e custo (v6)

| Métrica | A — estruturado | B — Zettelkasten | C — sem KB |
|---|---|---|---|
| Ações de retrieval (média/tarefa) | 6,4 | 6,8 | 0 |
| Notas lidas (média) | 1,8 | 5,2 | 0 |
| **Acerto de notas-ouro** | **0,27** | **0,93** | — |
| Tokens de prompt (média) | 14.033 | 18.458 | 721 |
| Duração por tarefa (média) | 123 s | 133 s | 63 s |

O padrão de retrieval replicou nas **4 rodadas**: B acha as notas certas em
~87–93% dos casos, A em ~27–47%; B lê 2–3× mais notas e custa ~30–40% mais
tokens. Na v6 a exploração rasa do A ficou ainda mais evidente (1,8 notas por
tarefa), e mesmo assim o score empatou — o modelo compensa parte do não-lido
com bom senso, mas perde exatamente as regras não-adivinháveis.

## 4. Conclusões

0. **Avaliar com Quarkus Dev MCP funciona e paga o custo.** A v6 provou que dá
   para dirigir continuous testing por MCP num harness automatizado: −47% de
   tempo por tarefa backend, feedback de compilação quase instantâneo para o
   loop de reparo, e detalhe por teste mais rico que o surefire (mensagem de
   falha + request/response HTTP). Recomendado como padrão do harness daqui em
   diante (`EVAL_MODE=devmcp`; `classic` mantido como fallback).

1. **Ter KB ≈ 3–6× o resultado — em todas as rodadas, com dois modelos diferentes.**
   O caso exemplar é o t3: uma nota atômica bem escrita sobre reenvio de convites
   produziu **5/5 nas duas vaults contra 0/5 do baseline** — transferência perfeita
   de regra de negócio para código. O baseline nunca acerta o que não dá para
   adivinhar (72h, códigos de erro, retenção de 30 dias).

2. **Zettelkasten vs. vault estruturado: empate técnico no score, perfis opostos.**
   - **B (Zettelkasten)** maximiza *recall*: os wikilinks funcionam como GPS — o
     modelo segue `[[link]]` e chega na regra, inclusive atravessando a nota
     contraditória até a correção. Foi o que lhe deu o t5 (achou a nota de badges;
     A não achou). Custo: mais notas lidas, mais tokens, mais tempo.
   - **A (estruturado)** maximiza *eficiência*: o `INDEX.md` roteia bem e barato,
     mas induz **exploração rasa** — o modelo lê 2–3 notas e para (no t1 leu
     limites de plano mas não convites, e chutou expiração de 7 dias).

3. **O gargalo é o modelo, não a organização.** O qwen3:8b morria em sintaxe Java
   (72% das tarefas com vault não compilavam); o coder:30b compila tudo, mas comete
   pecados de aderência (placeholder no lugar do header, ação de auditoria
   inventada). Com modelos locais desta faixa, a KB melhora muito o resultado, mas
   não fecha o gap até "produção".

### Recomendação prática

Para um time de engenharia montar KB para agentes: **híbrido A+B** — a estrutura de
pastas + INDEX do método A (controla custo de contexto e dá roteamento rápido) com a
disciplina de links densos do Zettelkasten (garante que o agente *chegue* na regra).
Toda nota deve linkar suas relacionadas; o índice existe para entrar, os links para
não sair cedo demais.

## 5. Respostas às perguntas originais

- **"O qwen 3 local consegue gerar código no ambiente Docker?"** Sim. Arquitetura
  validada: Ollama no host (GPU) + containers como clientes isolados
  (workspace/KB/toolchain por condição). Com 8 GB de VRAM não se roda 3 instâncias
  do modelo; compartilhar o modelo do host é também o desenho mais justo
  cientificamente.
- **"Zettelkasten ou por tema?"** Para agentes, empate em qualidade final nesta
  classe de modelo; escolha pelo custo (A) ou pelo recall (B) — ou o híbrido acima.

## 6. Achados de engenharia no caminho

- **Client proxy do Quarkus (causa da v4 descartada):** bean `@ApplicationScoped`
  com campos públicos → acesso a campo lê o *proxy*, chamada de método delega à
  instância real — dois estados distintos no "mesmo" objeto. Testes semeavam via
  campo, o código do modelo lia via método → 401 em tudo. Fix: `@jakarta.inject.Singleton`
  (sem proxy). Lição: nunca misturar estado em campos públicos com beans proxiados.
- **`Response.Status.UNPROCESSABLE_ENTITY` não existe** no JAX-RS — a KB ensinava
  422 e o modelo tropeçava na API; quem *não* lia a KB compilava por tentar menos.
  Mitigado com dica neutra de tecnologia no scaffold de referência (v3+).
- **`shutil.copytree` quebra os shims de `node_modules/.bin`** — `npx tsc` morre em
  workspace copiado; usar `node node_modules/typescript/lib/tsc.js`.
- **Coder-models misturam exploração e resposta final** — o protocolo precisa dar
  prioridade à exploração quando ACTION e FILE vêm juntos, ou o agente "responde"
  sem nunca ler a KB.
- **Dev MCP: contadores por-run enganam.** `getStatus.testsPassed` conta só o
  run incremental (continuous testing re-roda apenas os afetados) — um run
  incremental reporta 0 passados com tudo verde. O placar correto vem do estado
  cumulativo do `getTestResults` após um `runAll` explícito.
- **Dev MCP: fonte quebrada no boot = endpoint mudo.** Se o código não compila
  quando `quarkus:dev` sobe, o HTTP (e o `/q/dev-mcp`) nunca abre — mas o
  processo fica re-tentando compilar. O harness precisa tratar timeout de boot
  como erro de compilação reparável (o dev mode sobe sozinho quando o modelo
  corrige o arquivo).

## 7. Reproduzir

```powershell
# pré-requisitos: Docker Desktop + Ollama no host com o modelo desejado
docker compose build
docker compose run --rm bench-c   # baseline
docker compose run --rm bench-a   # vault estruturada
docker compose run --rm bench-b   # zettelkasten
python agent/report.py            # gera results/report.md

# variáveis: MODEL=qwen3:8b|qwen3-coder:30b  TASK_FILTER=t1,t3  SMOKE=1
#            EVAL_MODE=devmcp (padrão, Quarkus Dev MCP) | classic (mvn test frio)
```

Estrutura: `knowledge/` (as duas vaults), `tasks/` (enunciados + referência do
scaffold), `scaffold/` (Quarkus + Angular), `eval/` (31 testes), `agent/` (runner
agentic + gerador de relatório).
