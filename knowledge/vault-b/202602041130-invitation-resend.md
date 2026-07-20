# 202602041130 Invitation resend

Resend is ADMIN+, like every mutation ([[202601051030-tenant-roles]]).

- **Maximum 3 resends per invitation.** The 4th → 422 `RESEND_LIMIT_REACHED`,
  nothing changes. (Anti-spam: recipients complained about being bombarded.)
- Each resend increments `resendCount` and **resets `expiresAt` to now
  + 72h** — the [[202602041100-invitation-72h-expiry]] window restarts.
- Resending an already-expired invitation is allowed and **reactivates** it
  (fresh window). Forcing people to recreate the invitation makes no sense.
- Resend does NOT go through the plan limit check — the seat is already
  reserved ([[202605021430-pending-invitations-count]]).
- Audits `INVITATION_RESENT` ([[202601201300-mutation-audit-log]]).
