---
type: technical-convention
system: rate-limiting
status: active
updated: 2026-01-18
---

# Rate limit window semantics

Public API limits use a fixed 1-minute window. The outbound webhook limit
uses a **rolling** 60-minute window (not fixed-bucket) — see
[outbound-webhook-rate-limit.md](outbound-webhook-rate-limit.md).
