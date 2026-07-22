---
type: technical-convention
system: rate-limiting
status: active
updated: 2026-02-20
---

# Burst allowance

The public API allows a 2× burst for up to 5 seconds using a token-bucket
algorithm. The outbound webhook limit does NOT have a burst allowance — it's
a strict rolling-window count.
