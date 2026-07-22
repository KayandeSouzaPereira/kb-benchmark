---
type: technical-convention
system: webhooks
status: active
updated: 2026-05-20
---

# Webhook signing

Every webhook delivery is signed with **HMAC-SHA256** over the raw JSON body,
using the tenant's webhook secret. The signature is stored on the
`WebhookDelivery` record as a lowercase hex string (64 characters), with no
`sha256=` prefix and no colons — just the raw hex digest.

## When to use / When NOT to use

- Sign every delivery, including retries (recompute, do not reuse — the
  payload may include a fresh timestamp).
- Do NOT sign with the tenant's API key; webhook secret and API key are
  separate credentials.

## Related

- [retry-backoff-policy.md](retry-backoff-policy.md)
- [event-type-catalog.md](event-type-catalog.md)
- [../billing/payment-retry-and-webhooks.md](../billing/payment-retry-and-webhooks.md)
