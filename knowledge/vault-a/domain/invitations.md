---
type: business-rule
system: user-management
status: active
updated: 2026-05-02
---

# Invitation lifecycle

## Creation

- Only ADMIN+ creates invitations (see
  [roles-and-permissions](roles-and-permissions.md)).
- Respects the plan limit — a pending invitation counts as a seat
  (see [plan-limits](plan-limits.md)).
- **Every invitation expires in 72 hours** from creation:
  `expiresAt = createdAt + 72h`.
- An invitation is born with `status = PENDING` and `resendCount = 0`.
- Mandatory audit: action `USER_INVITED` (see [audit-log](audit-log.md)).

## Resend

- ADMIN+ only.
- **Maximum of 3 resends per invitation.** The 4th returns
  `422 RESEND_LIMIT_REACHED` and changes nothing.
- Each resend **resets the expiry to now + 72h** and increments `resendCount`.
- Resending an already-expired invitation is allowed and **reactivates** it
  (fresh 72h window).
- Mandatory audit: action `INVITATION_RESENT`.

## Acceptance

- Accepting an expired invitation returns `410 INVITATION_EXPIRED`.
- Acceptance creates the user with `status = ACTIVE` and marks the invitation
  as `ACCEPTED`.

## Anti-patterns already observed

- Applying the plan limit on resend (wrong: resend does not create a seat).
- Forgetting to reset `expiresAt` on resend.

## Related

- [roles-and-permissions](roles-and-permissions.md)
- [plan-limits](plan-limits.md)
- [audit-log](audit-log.md)
- [../code-standards/api-error-format.md](../code-standards/api-error-format.md)
