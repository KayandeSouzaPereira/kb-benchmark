---
type: adr
system: user-management
status: active
updated: 2026-03-15
---

# ADR-001 — User deletion is always soft-delete with 30-day retention

## Decision

Deleting a user = `status DELETED` + `deletedAt = now` + `purgeAt = now + 30 days`.
The record stays in the store until the purge job. Restoring within the window
is allowed (action `USER_RESTORED`).

## Context

B2B customers frequently delete users by mistake; compliance requires an intact
audit trail for at least 30 days.

## Discarded alternatives — do not propose again

- **Immediate hard delete**: breaks auditing and logical FKs; rejected.
- **90-day retention**: conflicts with LGPD/erasure requests; 30 days was the
  agreement with legal.
- **Boolean `deleted` flag**: insufficient — we need `purgeAt` for the purge
  job and `deletedAt` for reports.

## Related

- [../domain/user-deletion.md](../domain/user-deletion.md)
