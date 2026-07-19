---
tipo: regra-de-negocio
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# Exclusão de usuários (soft-delete)

**Não existe hard delete de usuário neste produto.** Decisão registrada em
[adr-001](../decisoes/adr-001-soft-delete-com-retencao.md).

## Regras

- Excluir um usuário significa: `status = DELETED`, `deletedAt = agora`,
  `purgeAt = agora + 30 dias`. O registro **permanece no store**.
- Somente ADMIN+ exclui, e apenas usuários do próprio tenant.
- ADMIN não pode excluir OWNER: `403 OWNER_PROTECTED`
  (ver [papeis-e-permissoes](papeis-e-permissoes.md)).
- **Ninguém exclui a si mesmo**: `422 CANNOT_DELETE_SELF` — evita tenant órfão
  por acidente e abuso de sessões roubadas.
- Sucesso responde `204 No Content`.
- Auditoria obrigatória: ação `USER_SOFT_DELETED` com `targetId` = id do usuário
  excluído (ver [auditoria](auditoria.md)).

## Quando usar / Quando NÃO usar

- Use em qualquer remoção de usuário disparada pela UI ou API.
- NÃO use para saída voluntária do tenant (fluxo "leave" tem regra própria
  de último owner).

## Anti-padrões já observados

- `store.users.remove(id)` — perde histórico e quebra auditoria. Nunca.
- Esquecer `purgeAt` — o job de purge definitivo depende desse campo.

## Relacionados

- [../decisoes/adr-001-soft-delete-com-retencao.md](../decisoes/adr-001-soft-delete-com-retencao.md)
- [papeis-e-permissoes](papeis-e-permissoes.md)
- [auditoria](auditoria.md)
