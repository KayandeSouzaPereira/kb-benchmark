---
type: technical-convention
system: rate-limiting
status: active
updated: 2026-02-02
---

# API key scopes

Keys are scoped `read`, `write`, or `admin`. Webhook secrets are a separate
credential type and have no scopes (they're not used for inbound auth).
