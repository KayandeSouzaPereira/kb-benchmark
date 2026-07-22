---
type: adr
system: notifications
status: active
updated: 2026-05-25
---

# ADR — payment_failed template retired in favor of payment_failed_v2

`payment_failed` (v1) had a broken invoice-link merge tag and was retired
2026-05-25. All code paths must use `payment_failed_v2`. Do not resurrect the
old template id.

## Related

- [email-template-mapping.md](email-template-mapping.md)
