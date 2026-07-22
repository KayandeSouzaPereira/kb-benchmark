---
type: technical-convention
system: webhooks
status: active
updated: 2026-04-01
---

# Event type catalog

Dot-separated, present tense on the resource, past tense on the action:
`user.invited`, `user.deleted`, `payment.failed`, `payment.succeeded`,
`subscription.cancelled`. Never reuse a retired event name — add a new one
and deprecate the old.
