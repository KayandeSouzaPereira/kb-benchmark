---
type: business-rule
system: sso
status: active
updated: 2026-04-08
---

# SAML just-in-time provisioning

First SSO login auto-creates a MEMBER user if the e-mail domain matches a
claimed domain (see [domain-claiming.md](domain-claiming.md)). Role is never
auto-elevated above MEMBER by JIT provisioning.
