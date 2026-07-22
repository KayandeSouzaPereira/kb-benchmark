---
type: business-rule
system: notifications
status: active
updated: 2026-04-14
---

# Notification dedup window

The same template + recipient combination is suppressed if already sent in
the last 10 minutes, to avoid duplicate sends from retried event processing.
