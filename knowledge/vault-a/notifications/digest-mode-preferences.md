---
type: business-rule
system: notifications
status: active
updated: 2026-05-25
---

# Digest mode preferences

Each tenant has a `notificationDigestMode`: `IMMEDIATE` (default) or
`DAILY_DIGEST`.

- `IMMEDIATE` → the notification is created with status **`SENT`** right
  away.
- `DAILY_DIGEST` → the notification is created with status **`QUEUED`** and
  picked up by the nightly digest job instead of sending immediately.

This applies to all transactional notifications, including billing events
like `payment.failed` — see
[../billing/payment-retry-and-webhooks.md](../billing/payment-retry-and-webhooks.md).
Critical security notifications (password reset, new device login) always
send immediately regardless of digest mode — see
[critical-vs-marketing.md](critical-vs-marketing.md).

## Related

- [email-template-mapping.md](email-template-mapping.md)
