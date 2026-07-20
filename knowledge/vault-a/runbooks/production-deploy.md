---
type: runbook
system: user-management
status: active
updated: 2026-02-20
---

# Runbook — production deploy

1. Merge to `main` triggers the pipeline (build + tests + image).
2. Canary deploy at 10% for 15 minutes; watch the 5xx error panel.
3. Full promotion, or automatic rollback if 5xx > 1%.
4. Migrations run before the canary, always backward-compatible.

On-call contact: `#oncall-users` channel.
