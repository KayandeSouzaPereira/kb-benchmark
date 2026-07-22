---
type: business-rule
system: webhooks
status: active
updated: 2026-03-09
---

# Webhook endpoint registration

Only ADMIN+ can register or change a tenant's webhook URL. URL must be
HTTPS; HTTP is rejected. One endpoint per tenant today (no per-event-type
routing yet).
