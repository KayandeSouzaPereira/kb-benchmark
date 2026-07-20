# 202602041100 Invitations expire in 72 hours

Every invitation is born PENDING with `resendCount = 0` and expires 72 hours
after creation: `expiresAt = createdAt + 72h`.

Why 72 and not 24/48: funnel data showed 31% of acceptances happen on day 2 or
3 (corporate invites wait for internal approval).

Accepting an already-expired invitation → 410 `INVITATION_EXPIRED`. Acceptance
creates the user as ACTIVE and marks the invitation ACCEPTED.

Who can create: ADMIN+ ([[202601051030-tenant-roles]]), respecting the seat
limit ([[202605021430-pending-invitations-count]]).
Every creation audits `USER_INVITED` ([[202601201300-mutation-audit-log]]).
Resend changes the expiry: [[202602041130-invitation-resend]].
