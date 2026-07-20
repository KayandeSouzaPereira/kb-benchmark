---
type: technical-convention
system: user-management
status: active
updated: 2026-04-11
---

# User status badges in the frontend

Everywhere a user status is displayed we use a badge with a **standardized CSS
class and pt-BR label**. Never show the raw enum (`ACTIVE` etc.) to the user.

The product UI is in Brazilian Portuguese — the labels below are the exact
strings and must not be translated:

| Status | CSS class | Displayed label |
|---|---|---|
| `ACTIVE` | `badge-success` | Ativo |
| `INVITED` | `badge-warning` | Convite pendente |
| `SUSPENDED` | `badge-muted` | Suspenso |
| `DELETED` | `badge-danger` | Excluído |

## Extra rule for DELETED

A deleted user shows, next to the badge, the definitive removal date:
`Remoção definitiva em {purgeAt}` formatted as **dd/MM/yyyy**
(in Angular: `{{ user.purgeAt | date:'dd/MM/yyyy' }}`).

## When to use / When NOT to use

- Use in every user list, card or detail view.
- Do NOT create per-screen color/text variations; the table above is canonical.

## Related

- [../domain/user-deletion.md](../domain/user-deletion.md)
