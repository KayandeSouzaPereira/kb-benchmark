---
type: technical-convention
system: user-management
status: active
updated: 2026-05-02
---

# API error format

Every business error responds JSON with this envelope:

```json
{ "code": "STABLE_CODE", "message": "free human text" }
```

`code` is a stable contract (clients switch on it); `message` may change.

## Code table

| HTTP | `code` | When |
|---|---|---|
| 403 | `FORBIDDEN_ROLE` | Actor without sufficient role (MEMBER attempting a mutation) |
| 403 | `OWNER_PROTECTED` | ADMIN trying to modify/delete an OWNER |
| 409 | `LAST_OWNER` | Operation would leave the tenant without an OWNER |
| 422 | `PLAN_LIMIT_EXCEEDED` | Plan seat limit reached |
| 422 | `CANNOT_DELETE_SELF` | Actor trying to delete their own account |
| 422 | `RESEND_LIMIT_REACHED` | 4th resend of the same invitation |
| 410 | `INVITATION_EXPIRED` | Accepting an expired invitation |
| 404 | `NOT_FOUND` | Nonexistent resource OR actor from another tenant (do not leak existence) |

## When to use / When NOT to use

- Use in every error `Response` of the REST resources.
- Do NOT invent new codes without an ADR; do NOT return stacktraces in the body.

## Related

- [../domain/roles-and-permissions.md](../domain/roles-and-permissions.md)
- [../domain/plan-limits.md](../domain/plan-limits.md)
- [../domain/invitations.md](../domain/invitations.md)
