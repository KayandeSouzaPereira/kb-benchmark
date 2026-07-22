---
type: technical-convention
system: webhooks
status: active
updated: 2026-01-15
---

# Custom headers on webhook requests

Every delivery includes `X-Webhook-Signature`, `X-Webhook-Event`,
`X-Webhook-Delivery-Id`. Tenants may not add custom headers today (no
per-tenant header config exists).
