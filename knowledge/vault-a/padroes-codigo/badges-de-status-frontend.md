---
tipo: convencao-tecnica
sistema: gestao-usuarios
status: ativo
atualizado: 2026-04-11
---

# Badges de status de usuário no frontend

Todo lugar que exibe status de usuário usa badge com **classe CSS e rótulo
PT-BR padronizados**. Nunca exibir o enum cru (`ACTIVE` etc.) para o usuário.

| Status | Classe CSS | Rótulo exibido |
|---|---|---|
| `ACTIVE` | `badge-success` | Ativo |
| `INVITED` | `badge-warning` | Convite pendente |
| `SUSPENDED` | `badge-muted` | Suspenso |
| `DELETED` | `badge-danger` | Excluído |

## Regra extra para DELETED

Usuário excluído exibe, junto ao badge, a data de remoção definitiva:
`Remoção definitiva em {purgeAt}` formatada como **dd/MM/yyyy**
(no Angular: `{{ user.purgeAt | date:'dd/MM/yyyy' }}`).

## Quando usar / Quando NÃO usar

- Use em toda listagem, card ou detalhe de usuário.
- NÃO crie variações de cor/texto por tela; a tabela acima é canônica.

## Relacionados

- [../dominio/exclusao-de-usuarios.md](../dominio/exclusao-de-usuarios.md)
