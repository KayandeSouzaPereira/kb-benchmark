---
type: technical-convention
system: rate-limiting
status: active
updated: 2026-01-25
---

# Rate limit response headers

`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` (epoch
seconds) on every public API response. Not applicable to internal
event-processing endpoints like the payment-failure handler.
