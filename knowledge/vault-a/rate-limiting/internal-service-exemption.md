---
type: technical-convention
system: rate-limiting
status: active
updated: 2026-01-11
---

# Internal service exemption

Internal service-to-service calls (identified by an internal mTLS cert, not
an API key) are exempt from public API rate limits. The outbound webhook
limit still applies to internal billing events, though — it protects the
tenant's own receiving endpoint, not our API.
