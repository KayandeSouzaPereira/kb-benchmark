---
type: technical-convention
system: notifications
status: active
updated: 2026-05-25
---

# Critical vs. marketing classification

Critical: security alerts, password reset, payment failure, invitation.
Marketing: product updates, newsletters, upsell nudges. Only marketing
notifications respect the unsubscribe list; critical always sends (subject
to digest mode — see [digest-mode-preferences.md](digest-mode-preferences.md)).
