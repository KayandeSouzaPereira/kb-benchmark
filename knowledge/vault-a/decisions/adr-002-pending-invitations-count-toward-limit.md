---
type: adr
system: user-management
status: active
updated: 2026-05-02
---

# ADR-002 — Pending invitations count toward the plan seat limit

## Decision

`occupied seats = non-DELETED users + PENDING invitations`. Applies to every
plan limit check.

## Context

Without this, a FREE tenant could invite 30 people and all of them could
accept, blowing past the plan. Billing and product decided on 2026-05-02 that
the seat is reserved at invitation time.

## Discarded alternatives — do not propose again

- **Count only active users**: allows blowing the plan via mass invitations
  (real bug from incident #482).
- **Block at acceptance**: terrible UX — the person clicks the email and only
  then finds out there is no seat.

## Related

- [../domain/plan-limits.md](../domain/plan-limits.md)
- [../domain/invitations.md](../domain/invitations.md)
