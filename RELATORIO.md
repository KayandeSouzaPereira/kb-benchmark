# Relatório final — Benchmark de Knowledge Base para agentes de código

**Data:** 2026-07-19 a 2026-07-20 · **Autor:** benchmark automatizado (Claude Code + Ollama local)
**Local:** `C:\dev\kb-benchmark` · **Dados brutos:** `results/` (v7), `results-v2/`, `results-v3/`, `results-v4-invalid/`, `results-v5/`, `results-v6/`, `results-v7-runs/` (confirmação estatística de 11 rodadas)

*(Versão em inglês: [REPORT.md](REPORT.md). Os dois são mantidos sincronizados; em caso de divergência, este arquivo é a fonte da verdade.)*

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
| v6 | qwen3-coder:30b | avaliação via **Quarkus Dev MCP** (Quarkus 3.33 LTS) | 12/31 (39%) | 13/31 (42%) | 2/31 (6%) |
| **v7 (definitiva)** | **qwen3-coder:30b** | **KB e prompts em inglês** + dica `@HeaderParam` | **21/31 (68%)** | **15/31 (48%)** | **8/31 (26%)** |

### v7: inglês + dica de header — o maior salto do benchmark

| Tarefa | A | B | C |
|---|---|---|---|
| t1 — Criar convite | **4/6** | **4/6** | 1/6 |
| t2 — Excluir usuário | **4/7** | 3/7 | 2/7 |
| t3 — Reenviar convite | **5/5** | 0/5 † | 0/5 |
| t4 — Alterar papel | **6/6** | **6/6** | 3/6 |
| t5 — Badges Angular | 2/7 | 2/7 | 2/7 |

† A vault-b leu as duas notas-ouro do reenvio (retrieval perfeito), mas
declarou `@Consumes(APPLICATION_JSON)` num POST sem corpo → 415 em todos os
testes. Sem esse único deslize de API, A e B empatariam em 20/31.

Mudanças da v7 e atribuição dos ganhos:

- **Tudo em inglês** (conteúdo E nomes de arquivo das vaults, enunciados,
  prompts do agente). Rótulos de badge permanecem pt-BR como regra de produto
  explícita ("do not translate").
- **Dica neutra de `@HeaderParam`** com exemplo de assinatura no scaffold de
  referência — destravou o t4 nos 3 casos (0→3/6/6): era o stub/`@Context`
  errado que zerava a tarefa desde a v5.
- Descontando o efeito da dica (t4), o **idioma responde pelo resto do salto**:
  t1 0→4, t2 1-2→3-4 nos casos com vault, e o retrieval do vault estruturado
  saltou de 27% para **67% de acerto de notas-ouro** — nomes de arquivo em
  inglês são muito melhor navegados pelo modelo. Tokens por tarefa caíram ~30%
  (inglês é mais denso) e a duração média por tarefa backend caiu junto.
- Primeira rodada em que A > B no placar (21 vs 15), mas a diferença é quase
  toda o acidente do t3 (†) — o veredito honesto continua "empate técnico com
  perfis diferentes", agora com A navegando tão bem quanto B (gold-hit 0,67 ×
  0,67) e gastando menos.

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

## 3.5. Confirmação estatística — 11 rodadas independentes (v7)

Uma única rodada não separa efeito real de sorte de amostragem — um coder-model
de 30B tem variância de sampling considerável. Para confirmar os números da
v7, rodei **10 rodadas adicionais independentes** com exatamente a mesma
configuração (qwen3-coder:30b, KB em inglês, avaliação via Dev MCP, dica de
`@HeaderParam`), somadas à rodada já publicada (`round-00`) — 11 pontos de
dados no total. Dados brutos em `results-v7-runs/`, agregação completa em
[`results-v7-runs/AGGREGATE.md`](results-v7-runs/AGGREGATE.md).

### Placar total por rodada (31 testes)

| Rodada | C — Sem KB | A — Vault estruturado | B — Zettelkasten |
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
| **Média ± desvio** | **7,5 ± 0,8** | **23,3 ± 1,9** | **18,8 ± 3,4** |
| **Min–Max** | 6–8 | 21–26 | 15–25 |

### O que a amostra maior confirma e corrige

1. **O efeito da KB é inquestionável.** Em 11 rodadas independentes, o
   intervalo do baseline (6–8) e o da pior vault (15–25 para B, 21–26 para A)
   **nunca se sobrepõem**. Não é sorte de uma rodada — é um efeito de ~3× que
   se repete sempre.

2. **A vault estruturada (A) é consistentemente melhor que o Zettelkasten (B)
   — isso corrige a conclusão de "empate técnico" da v7 original.** Com só
   uma rodada, A=21 e B=15 pareciam ruído; com 11, A nunca caiu abaixo de 21
   e B nunca passou de 25, com médias de 23,3 vs 18,8 (diferença de +4,5
   pontos, tamanho de efeito ≈1,6 desvios-padrão combinados — grande pela
   convenção estatística usual). B tem quase o dobro do desvio-padrão de A
   (3,4 vs 1,9): A não é só melhor, é mais **previsível**.

3. **A vantagem de A não é retrieval — as duas acham as notas certas quase
   igualmente bem** (gold-hit médio: A 0,69, B 0,68, quase idêntico ao longo
   das 11 rodadas). A diferença está a jusante, na geração de código a partir
   do que foi lido.

4. **Padrão por tarefa é estável e revela uma divisão de forças real:**

   | Tarefa | A (média±dp) | B (média±dp) | Quem vence |
   |---|---|---|---|
   | t1 — Criar convite | 5,5±0,9/6 | 4,3±1,1/6 | **A**, folgado |
   | t2 — Excluir usuário | 6,7±0,9/7 | 3,9±0,3/7 | **A**, folgado |
   | t3 — Reenviar convite | **5,0±0,0/5** | 2,7±2,5/5 | **A**, e sem nenhuma variância |
   | t4 — Alterar papel | 4,1±1,4/6 | **5,5±1,7/6** | **B** |
   | t5 — Badges Angular | 2,0±0,0/7 | 2,5±1,4/7 | B, levemente |

5. **Achado extra: o t3 da vault-b é literalmente bimodal — 0/5 ou 5/5, nunca
   meio-termo** (6 rodadas em 5/5, 5 em 0/5). Investigado: em **100% das
   rodadas** o modelo leu as duas notas-ouro corretas do reenvio. A causa é um
   coin-flip de geração de código — em algumas rodadas o modelo anota o
   `@Path` do reenvio com `@Consumes(APPLICATION_JSON)` herdado da classe,
   que rejeita com `415` o `POST` de reenvio (que não tem corpo). Não é falha
   de conhecimento; é inconsistência de sintaxe JAX-RS specífica desse
   endpoint. Explica sozinho o desvio-padrão gigante de B no t3 (2,5) contra
   zero de A.

6. **O t5 (Angular) do vault A é suspeitosamente flat**: exatos 2/7 em
   **todas as 11 rodadas**, zero variância — indício de um teto sistemático
   (provavelmente o mesmo padrão de resposta incompleta visto na v5/vault-b,
   agora reproduzido de forma consistente pelo lado A) mais do que uma
   coincidência estatística.

### Veredito revisado

A conclusão "empate técnico A≈B" das rodadas anteriores **não se sustenta**
com 11 amostras: **A vence com folga e mais consistência** no agregado, muito
por causa de dois pontos fortes (t2, t3) onde A é quase perfeito e B sofre com
um bug de sintaxe reproduzível. B ainda vence claramente em t4 e levemente em
t5. Isto é: a organização da KB não é neutra para este modelo — o vault
estruturado com `INDEX.md` produz resultados melhores e mais estáveis na
maioria das tarefas deste benchmark, mesmo com acerto de retrieval
equivalente ao Zettelkasten.

## 4. Conclusões

0. **O idioma da KB importa — muito.** Traduzir vaults (conteúdo e nomes de
   arquivo), enunciados e prompts de PT-BR para inglês levou o benchmark de
   12-13/31 para 15-21/31 nos casos com KB (e o baseline de 2 para 8, somado à
   dica de header). O efeito mais nítido foi no retrieval por filesystem: com
   nomes de arquivo em inglês, o vault estruturado saltou de 27% para 67% de
   acerto de notas-ouro — o modelo navega semanticamente pelos nomes, e nomes
   em português eram um atrito invisível. Para KBs consumidas por agentes,
   escreva em inglês (mantendo strings de produto no idioma do produto, como
   regra explícita).

1. **Avaliar com Quarkus Dev MCP funciona e paga o custo.** A v6 provou que dá
   para dirigir continuous testing por MCP num harness automatizado: −47% de
   tempo por tarefa backend, feedback de compilação quase instantâneo para o
   loop de reparo, e detalhe por teste mais rico que o surefire (mensagem de
   falha + request/response HTTP). Recomendado como padrão do harness daqui em
   diante (`EVAL_MODE=devmcp`; `classic` mantido como fallback).

2. **Ter KB ≈ 2–6× o resultado — em todas as rodadas, com dois modelos diferentes.**
   O caso exemplar é o t3: uma nota atômica bem escrita sobre reenvio de convites
   produziu **5/5 nas duas vaults contra 0/5 do baseline** — transferência perfeita
   de regra de negócio para código. O baseline nunca acerta o que não dá para
   adivinhar (72h, códigos de erro, retenção de 30 dias).

3. **Zettelkasten vs. vault estruturado: com 1 rodada parecia empate; com 11
   independentes (§3.5), o vault estruturado vence com folga e mais
   consistência.**
   - **A (estruturado)** venceu 3 das 5 tarefas por margens grandes (t1, t2,
     t3) e com desvio-padrão bem menor no total (1,9 vs 3,4) — é a opção mais
     previsível.
   - **B (Zettelkasten)** venceu t4 e levemente t5, mas com o dobro da
     variância de A — inclusive um caso bimodal no t3 (0/5 ou 5/5, nunca
     meio-termo) causado por um bug reproduzível de anotação JAX-RS, não por
     falha de conhecimento.
   - A diferença **não é retrieval**: as duas acham as notas-ouro certas quase
     igualmente bem (gold-hit ~0,68–0,69 nas 11 rodadas). A vantagem de A está
     inteiramente a jusante, na tradução de "li a regra certa" para "gerei
     código correto de primeira".

4. **O gargalo é o modelo, não a organização.** O qwen3:8b morria em sintaxe Java
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
