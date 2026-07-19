---
tipo: convencao-tecnica
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# Formato de erros da API

Todo erro de negócio responde JSON com este envelope:

```json
{ "code": "CODIGO_ESTAVEL", "message": "texto humano livre" }
```

`code` é contrato estável (clientes fazem switch nele); `message` pode mudar.

## Tabela de códigos

| HTTP | `code` | Quando |
|---|---|---|
| 403 | `FORBIDDEN_ROLE` | Ator sem papel suficiente (MEMBER tentando mutação) |
| 403 | `OWNER_PROTECTED` | ADMIN tentando alterar/excluir um OWNER |
| 409 | `LAST_OWNER` | Operação deixaria o tenant sem OWNER |
| 422 | `PLAN_LIMIT_EXCEEDED` | Limite de assentos do plano atingido |
| 422 | `CANNOT_DELETE_SELF` | Ator tentando excluir a própria conta |
| 422 | `RESEND_LIMIT_REACHED` | 4º reenvio do mesmo convite |
| 410 | `INVITATION_EXPIRED` | Aceitação de convite expirado |
| 404 | `NOT_FOUND` | Recurso inexistente OU ator de outro tenant (não vazar existência) |

## Quando usar / Quando NÃO usar

- Use em todo `Response` de erro dos recursos REST.
- NÃO invente códigos novos sem ADR; NÃO retorne stacktrace no body.

## Relacionados

- [../dominio/papeis-e-permissoes.md](../dominio/papeis-e-permissoes.md)
- [../dominio/limites-de-plano.md](../dominio/limites-de-plano.md)
- [../dominio/convites.md](../dominio/convites.md)
