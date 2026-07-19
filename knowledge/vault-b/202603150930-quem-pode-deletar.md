# 202603150930 Quem pode excluir usuário

- ADMIN+ do próprio tenant ([[202601051030-papeis-do-tenant]],
  [[202602151100-isolamento-de-tenant-404]]).
- ADMIN não exclui OWNER → 403 `OWNER_PROTECTED`
  ([[202602101415-protecao-do-owner]]).
- **Ninguém exclui a si mesmo** → 422 `CANNOT_DELETE_SELF`. Dois motivos:
  evita tenant órfão por engano e limita estrago de sessão roubada.
- A exclusão em si é sempre soft ([[202603150900-soft-delete-30-dias]]) e
  audita `USER_SOFT_DELETED` com targetId = usuário excluído
  ([[202601201300-auditoria-de-mutacoes]]).
