---
type: technical-convention
system: sso
status: active
updated: 2026-03-14
---

# IdP-initiated vs SP-initiated flow

Both supported. IdP-initiated requires a `RelayState` pointing at a
allowlisted path to prevent open-redirect abuse.
