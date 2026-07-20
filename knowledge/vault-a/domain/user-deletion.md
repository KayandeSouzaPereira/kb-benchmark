---
type: business-rule
system: user-management
status: active
updated: 2026-05-02
---

# User deletion (soft-delete)

**There is no hard delete of users in this product.** Decision recorded in
[adr-001](../decisions/adr-001-soft-delete-with-retention.md).

## Rules

- Deleting a user means: `status = DELETED`, `deletedAt = now`,
  `purgeAt = now + 30 days`. The record **stays in the store**.
- Only ADMIN+ deletes, and only users of their own tenant.
- An ADMIN cannot delete an OWNER: `403 OWNER_PROTECTED`
  (see [roles-and-permissions](roles-and-permissions.md)).
- **Nobody deletes themselves**: `422 CANNOT_DELETE_SELF` — prevents accidental
  orphan tenants and abuse of stolen sessions.
- Success responds `204 No Content`.
- Mandatory audit: action `USER_SOFT_DELETED` with `targetId` = id of the
  deleted user (see [audit-log](audit-log.md)).

## When to use / When NOT to use

- Use for any user removal triggered by the UI or API.
- Do NOT use for voluntarily leaving a tenant (the "leave" flow has its own
  last-owner rule).

## Anti-patterns already observed

- `store.users.remove(id)` — loses history and breaks auditing. Never.
- Forgetting `purgeAt` — the definitive purge job depends on that field.

## Related

- [../decisions/adr-001-soft-delete-with-retention.md](../decisions/adr-001-soft-delete-with-retention.md)
- [roles-and-permissions](roles-and-permissions.md)
- [audit-log](audit-log.md)
