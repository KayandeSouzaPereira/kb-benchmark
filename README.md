# kb-benchmark

Benchmark: qual organização de knowledge base (Obsidian/Markdown) serve melhor
como fonte de contexto para um agente de código local (qwen3 via Ollama)?

**Relatório completo:** [RELATORIO.md](RELATORIO.md) (português) ·
[REPORT.md](REPORT.md) (English)

## Condições

| Caso | Serviço | Knowledge base |
|---|---|---|
| A | `bench-a` | Vault estruturado para agentes: pastas semânticas, `INDEX.md` roteador, kebab-case, frontmatter, seções padronizadas |
| B | `bench-b` | Zettelkasten clássico: notas atômicas com ID timestamp, wikilinks densos, structure notes, notas contraditórias com correção posterior |
| C | `bench-c` | Sem knowledge base |

O conteúdo de regras de negócio é idêntico em A e B — muda só a organização.
Domínio: SaaS multi-tenant de gestão de usuários (papéis, limites de plano,
convites, soft-delete, auditoria). O agente gera código Quarkus 3 (4 tarefas)
e Angular 18 (1 tarefa), avaliado por testes JUnit/RestAssured black-box e
checagens estáticas + tsc.

O modelo explora a vault com um protocolo agentic de texto
(`ACTION: ls|grep|read`, máx. 8 passos) — exatamente o fluxo de um agente de
código sobre filesystem.

## Pré-requisitos

- Ollama no host com `qwen3:8b` (`ollama pull qwen3:8b`)
- Docker Desktop

## Rodar

```powershell
docker compose build            # ~5-10 min na primeira vez (aquece Maven/npm)
$env:SMOKE="1"; docker compose run --rm bench-c; $env:SMOKE=""   # sanity check

docker compose run --rm bench-c   # baseline
docker compose run --rm bench-a   # vault estruturado
docker compose run --rm bench-b   # zettelkasten

python agent/report.py            # gera results/report.md
```

Variáveis úteis: `TASK_FILTER=t1,t2` roda um subconjunto; `MODEL=...` troca o
modelo.

Resultados por tarefa (score, retrieval, tokens, transcript completo) ficam em
`results/<caso>/`.
