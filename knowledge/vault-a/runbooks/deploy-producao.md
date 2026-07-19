---
tipo: runbook
sistema: gestao-usuarios
status: ativo
atualizado: 2026-02-20
---

# Runbook — deploy em produção

1. Merge na `main` dispara pipeline (build + testes + imagem).
2. Deploy canário em 10% por 15 minutos; observar painel de erros 5xx.
3. Promoção total ou rollback automático se 5xx > 1%.
4. Migrations rodam antes do canário, sempre backward-compatible.

Contato de plantão: canal `#oncall-users`.
