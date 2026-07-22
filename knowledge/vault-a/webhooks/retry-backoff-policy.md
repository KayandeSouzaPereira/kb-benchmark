---
type: business-rule
system: webhooks
status: active
updated: 2026-05-20
---

# Webhook retry / backoff policy

Every new `WebhookDelivery` is created with **`maxAttempts = 5`** and
`attemptCount = 0`. Delivery starts in status `PENDING` (or `DEFERRED` if the
tenant is rate-limited — see
[../rate-limiting/outbound-webhook-rate-limit.md](../rate-limiting/outbound-webhook-rate-limit.md)).

Retries use exponential backoff: 1min, 5min, 30min, 2h, 12h. After
`maxAttempts` failed deliveries the record moves to status `FAILED` and the
endpoint is flagged — see
[endpoint-disabling-on-failures.md](endpoint-disabling-on-failures.md).

## Related

- [webhook-signing.md](webhook-signing.md)
