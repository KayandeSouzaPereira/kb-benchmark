# INDEX — Team knowledge base (SaaS user management)

Read this file first. It maps what lives in each folder and when to consult it.

| Folder | Contents | When to consult |
|---|---|---|
| `domain/` | Product business rules: roles and permissions, plan limits, invitations, user deletion, audit log, authentication | Before implementing ANY endpoint or screen that touches users, invitations or roles |
| `billing/` | Subscriptions, payment failures, proration, refunds, invoicing, trials | Before implementing anything related to charges, plans, invoices or payment events |
| `webhooks/` | Webhook signing, retry/backoff, event catalog, endpoint lifecycle | Before creating or delivering any `WebhookDelivery` |
| `notifications/` | Email/in-app notification templates, digest mode, bounce handling | Before sending or queueing any notification |
| `rate-limiting/` | API and webhook rate limits, API keys, abuse detection | Before creating a `WebhookDelivery` or any rate-limited resource |
| `sso/` | SAML/SCIM identity federation, JIT provisioning, break-glass access | Only for SSO/identity-federation work — not needed for billing, webhooks or notifications |
| `code-standards/` | Team technical conventions: API error format, frontend status badges | Whenever returning an HTTP error or rendering status in the UI |
| `decisions/` | ADRs — architectural decisions with discarded alternatives | When a rule seems odd or you want to propose something different |
| `product/` | Product material: plans and pricing | Commercial context; rarely needed for code |
| `runbooks/` | Operational procedures (deploy etc.) | Operations, not development |

**Cross-cutting events** (e.g. a payment failure that must trigger a webhook
AND a notification AND respect a rate limit) touch multiple folders at once —
each relevant note links to the others it depends on under "Related". Follow
those links; do not assume one folder is self-contained for such flows.

## Files in the core folders (domain, code-standards, decisions, product, runbooks)

- `domain/roles-and-permissions.md` — OWNER/ADMIN/MEMBER hierarchy, who can do what, owner protections
- `domain/plan-limits.md` — how many users each plan allows and what counts toward the limit
- `domain/invitations.md` — invitation lifecycle: expiry, resend, acceptance
- `domain/user-deletion.md` — soft-delete, retention, who can delete
- `domain/audit-log.md` — what to audit and the mandatory AuditEntry format
- `domain/authentication-and-lockout.md` — password policy and account lockout
- `code-standards/api-error-format.md` — JSON error envelope + table of codes and HTTP statuses
- `code-standards/frontend-status-badges.md` — CSS classes and pt-BR labels per user status
- `decisions/adr-001-soft-delete-with-retention.md` — why there is never a hard delete
- `decisions/adr-002-pending-invitations-count-toward-limit.md` — why a pending invite occupies a seat
- `product/plans-and-pricing.md` — Free / Pro / Enterprise
- `runbooks/production-deploy.md` — deploy pipeline

## billing/, webhooks/, notifications/, rate-limiting/, sso/

These folders grew fast and are **not exhaustively indexed here** — each has
around 10 notes. `ls` the specific folder you need; every note's "Related"
section links to the other notes it depends on, so once you find one
relevant note in a folder you can usually navigate to the rest from there
instead of reading the whole folder.
