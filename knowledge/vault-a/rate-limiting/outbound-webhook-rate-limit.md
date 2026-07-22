---
type: business-rule
system: rate-limiting
status: active
updated: 2026-05-28
---

# Outbound webhook rate limit

Each tenant may have at most **10 webhook deliveries created in a rolling
60-minute window**. When creating a new `WebhookDelivery` (any event type),
count existing deliveries for that tenant with `createdAt` within the last
60 minutes; if the count is **already at or above 10**, the new delivery is
created with status **`DEFERRED`** instead of `PENDING` (it is NOT rejected
or dropped — it's just queued behind the limit for later processing).

This check happens regardless of the event type, and applies before signing
— see
[../webhooks/webhook-signing.md](../webhooks/webhook-signing.md) and
[../billing/payment-retry-and-webhooks.md](../billing/payment-retry-and-webhooks.md).

## Related

- [per-plan-rate-tiers.md](per-plan-rate-tiers.md)
