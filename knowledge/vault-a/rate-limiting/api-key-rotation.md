---
type: business-rule
system: rate-limiting
status: active
updated: 2026-03-12
---

# API key rotation

API keys (used for the public REST API, not webhooks) can have 2 active keys
per tenant simultaneously to allow zero-downtime rotation. Old key must be
revoked manually after rotation; there's no auto-expiry.
