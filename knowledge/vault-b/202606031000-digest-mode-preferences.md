# 202606031000 Digest mode preferences

Tenant has `notificationDigestMode`: `IMMEDIATE` (default) or
`DAILY_DIGEST`.

- `IMMEDIATE` → notification created with status **`SENT`** right away.
- `DAILY_DIGEST` → created with status **`QUEUED`**, picked up by the
  nightly digest job.

Applies to transactional notifications too, including billing events like
payment failure ([[202606010930-payment-failure-handling]]). Exception:
critical security notifications (password reset, new device) always send
immediately regardless of digest mode — see
[[202606031230-critical-vs-marketing]].

Related: [[202606030930-email-template-mapping]].
