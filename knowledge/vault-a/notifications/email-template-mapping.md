---
type: technical-convention
system: notifications
status: active
updated: 2026-05-25
---

# Email template mapping

Business events map to template IDs. For payment failure:
**`templateId = "payment_failed_v2"`** (not `payment_failed` — that template
was retired, see [template-catalog-history.md](template-catalog-history.md)).

| Event | Template ID |
|---|---|
| `payment.failed` | `payment_failed_v2` |
| `user.invited` | `invite_v3` |
| `subscription.cancelled` | `cancellation_confirmed_v1` |

## Related

- [digest-mode-preferences.md](digest-mode-preferences.md)
- [../billing/payment-retry-and-webhooks.md](../billing/payment-retry-and-webhooks.md)
