---
type: technical-convention
system: notifications
status: active
updated: 2026-03-05
---

# Notification locale selection

Uses the recipient user's profile locale if set, else the tenant's default
locale, else `en-US`. Never the sender/actor's locale.
