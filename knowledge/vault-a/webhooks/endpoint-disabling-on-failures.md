---
type: business-rule
system: webhooks
status: active
updated: 2026-05-20
---

# Disabling endpoints after repeated failures

If 3 consecutive deliveries reach status `FAILED` (all retries exhausted),
the tenant's webhook endpoint is auto-disabled and an in-app notification is
sent to admins. Re-enabling requires an explicit admin action.

## Related

- [retry-backoff-policy.md](retry-backoff-policy.md)
