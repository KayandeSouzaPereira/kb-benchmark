---
type: technical-convention
system: webhooks
status: active
updated: 2026-02-11
---

# Webhook payload versioning

Every payload includes `"apiVersion": "2026-01-01"`. Breaking payload
changes ship as a new dated version; tenants opt in via dashboard setting.
Non-breaking additive fields do not bump the version.
