---
type: business-rule
system: webhooks
status: active
updated: 2026-02-25
---

# Webhook secret rotation

Rotating a webhook secret keeps the old secret valid for 24h (dual-signing
window) so in-flight retries with the old signature still validate. After
24h only the new secret is accepted.
