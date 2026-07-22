---
type: business-rule
system: billing
status: active
updated: 2026-02-28
---

# Payment method update

Updating the payment method does not retry any currently failed invoice
automatically — the tenant (or admin) must explicitly retry from the billing
page. This is intentional: avoids surprise charges right after a card update.
