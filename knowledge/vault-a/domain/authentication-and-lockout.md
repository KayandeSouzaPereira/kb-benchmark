---
type: business-rule
system: user-management
status: active
updated: 2026-03-10
---

# Authentication and lockout

## Password policy

- Minimum 12 characters, at least 1 digit and 1 symbol.
- History: the last 5 passwords cannot be reused.

## Lockout

- 5 consecutive failed login attempts lock the account for 15 minutes.
- The counter resets after a successful login or lock expiry.
- Manual unlock by ADMIN+ is allowed and is audited.

## Related

- [roles-and-permissions](roles-and-permissions.md)
- [audit-log](audit-log.md)
