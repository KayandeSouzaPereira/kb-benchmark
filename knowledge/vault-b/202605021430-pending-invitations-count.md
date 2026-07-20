# 202605021430 Correction: pending invitations DO count toward the limit

Final decision with billing and product (2026-05-02 meeting), correcting my
intuition from [[202603121015-pending-invites-limit-doubt]]:

**occupied seats = users with status != DELETED + PENDING invitations.**

The seat is reserved at invitation time. Reason: without this, a FREE tenant
invited 30 people and they all accepted (incident #482 bug). Blocking at
acceptance would be horrible UX.

Practical consequence: creating an invitation when occupied >= plan maximum →
422 `PLAN_LIMIT_EXCEEDED` ([[202601121000-plan-seat-limits]]).
Resend does NOT go through this check — it creates no new seat
([[202602041130-invitation-resend]]).
