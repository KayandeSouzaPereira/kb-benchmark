---
tipo: adr
sistema: gestao-usuarios
status: ativo
atualizado: 2026-03-15
---

# ADR-001 — Exclusão de usuário é sempre soft-delete com retenção de 30 dias

## Decisão

Excluir usuário = `status DELETED` + `deletedAt = agora` + `purgeAt = agora + 30 dias`.
O registro fica no store até o job de purge. Restauração dentro da janela é
permitida (ação `USER_RESTORED`).

## Contexto

Clientes B2B excluem usuários por engano com frequência; compliance exige
trilha de auditoria íntegra por no mínimo 30 dias.

## Alternativas descartadas — não propor novamente

- **Hard delete imediato**: quebra auditoria e FK lógicas; rejeitado.
- **Retenção de 90 dias**: conflita com pedidos de LGPD/erasure; 30 dias foi o
  acordo com jurídico.
- **Flag booleana `deleted`**: insuficiente — precisamos de `purgeAt` para o job
  de purge e de `deletedAt` para relatórios.

## Relacionados

- [../dominio/exclusao-de-usuarios.md](../dominio/exclusao-de-usuarios.md)
