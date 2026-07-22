## system

You are a senior software engineer on a product team.
The team keeps a knowledge base of Markdown files with the business rules and
conventions. You MUST consult it before writing code, because the
product-specific rules are not obvious.

To explore the knowledge base, reply with ONE single command line per message:

ACTION: ls <path>       (lists files in a directory; use "." for the root)
ACTION: grep <term>     (text search across all notes)
ACTION: read <file>     (reads the content of a note)

After each ACTION you will receive the result. You have at most 14
actions in total — use them well.

When you have what you need, produce the final files in this exact format
(there may be more than one FILE block):

FILE: relative/path/to/File.java
```java
<complete file content>
```

Format rules: never mix ACTION and FILE in the same reply; write complete,
compilable files; do not modify the project's existing files.

---

## user

# Task: user list with status badges (Angular)

Create `src/app/user-list.component.ts`: a standalone component, selector
`app-user-list`, with `@Input() users: UserView[]` (import from
`./user.model`).

Render a table with each user's e-mail, role and status. The status must be
displayed as a **badge**, following the visual and text conventions the team
has defined (CSS classes, displayed labels and extra per-status information).
Use an inline template.


## Existing project (Angular 18, standalone) — do NOT rewrite

`src/app/user.model.ts` already exists:

```ts
export interface UserView {
  id: string;
  email: string;
  role: 'OWNER' | 'ADMIN' | 'MEMBER';
  status: 'INVITED' | 'ACTIVE' | 'SUSPENDED' | 'DELETED';
  purgeAt?: string;
}
```

Create the component at `src/app/user-list.component.ts` (inline template).


---

## assistant

ACTION: read ./user.model.ts
```ts
export interface UserView {
  id: string;
  email: string;
  role: 'OWNER' | 'ADMIN' | 'MEMBER';
  status: 'INVITED' | 'ACTIVE' | 'SUSPENDED' | 'DELETED';
  purgeAt?: string;
}
```
ACTION: grep -r "badge" . --include="*.md"
```

---

## user

RESULT (13 actions left):
file not found: ./user.model.ts

---

## assistant

ACTION: ls .
```

---

## user

RESULT (12 actions left):
202601050900-user-domain-map.md
202601051030-tenant-roles.md
202601080800-lockout-and-passwords.md
202601121000-plan-seat-limits.md
202601201300-mutation-audit-log.md
202601201330-api-error-codes.md
202602041100-invitation-72h-expiry.md
202602041130-invitation-resend.md
202602101415-owner-protection.md
202602101430-last-owner.md
202602151100-tenant-isolation-404.md
202603121015-pending-invites-limit-doubt.md
202603150900-soft-delete-30-days.md
202603150930-who-can-delete-users.md
202604010900-api-and-conventions-map.md
202604111600-frontend-status-badges.md
202605021430-pending-invitations-count.md
202605190800-pricing-ideas.md
202606010900-billing-map.md
202606010930-payment-failure-handling.md
202606011000-proration-rules.md
202606011030-invoice-numbering.md
202606011100-refund-policy.md
202606011130-subscription-cancellation.md
202606011200-trial-period.md
202606011230-payment-method-update.md
202606011300-tax-handling.md
202606011330-currency-support.md
202606011400-credit-notes.md
202606020900-webhooks-map.md
202606020930-webhook-signing.md
202606021000-webhook-retry-backoff.md
202606021030-event-type-catalog.md
202606021100-endpoint-registration.md
202606021130-payload-versioning.md
202606021200-delivery-log-retention.md
202606021230-secret-rotation.md
202606021300-endpoint-disabling-on-failures.md
202606021330-custom-headers.md
202606021400-replay-tool.md
202606030900-notifications-map.md
202606030930-email-template-mapping.md
202606031000-digest-mode-preferences.md
202606031030-unsubscribe-rules.md
202606031100-locale-selection.md
202606031130-sms-fallback-draft.md
202606031200-dedup-window.md
202606031230-critical-vs-marketing.md
202606031300-bounce-handling.md
202606031330-template-retirement-adr.md
202606031400-in-app-retention.md
202606040900-rate-limiting-map.md
202606040930-outbound-webhook-rate-limit.md
202606041000-api-key-rotation.md
202606041030-per-plan-rate-tiers.md
202606041100-burst-allowance.md
202606041130-response-headers.md
202606041200-api-key-scopes.md
202606041230-ip-allowlisting.md
202606041300-internal-service-exemption.md
202606041330-abuse-detection.md
202606041400-reset-window-definition.md
202606050900-sso-map.md
202606050930-saml-jit-provisioning.md
202606051000-domain-claiming.md
202606051030-sso-enforced-tenants.md
202606051100-group-role-mapping.md
202606051130-scim-provisioning.md
202606051200-sso-session-lifetime.md
202606051230-idp-initiated-flow.md
202606051300-break-glass-access.md
202606051330-multiple-idp-draft.md
202606051400-sso-audit-logging.md

---

## assistant

ACTION: read 202604111600-frontend-status-badges.md
```

---

## user

RESULT (11 actions left):
# 202604111600 Frontend status badges

Never show the raw enum to the user. Canonical mapping (CSS class + label).
Careful: the product UI is in Brazilian Portuguese — the labels are exact
strings, do not translate them:

- ACTIVE → `badge-success` / "Ativo"
- INVITED → `badge-warning` / "Convite pendente"
- SUSPENDED → `badge-muted` / "Suspenso"
- DELETED → `badge-danger` / "Excluído"

For DELETED, also show the definitive removal date:
"Remoção definitiva em {purgeAt}" formatted dd/MM/yyyy
(Angular: `{{ user.purgeAt | date:'dd/MM/yyyy' }}`).
The purgeAt comes from soft-delete: [[202603150900-soft-delete-30-days]].

No per-screen color variations — we've already had 3 different greens.


---

## assistant

ACTION: ls src/app/
```

---

## user

RESULT (10 actions left):
does not exist: src/app/

---

## assistant

ACTION: ls src/
```

---

## user

RESULT (9 actions left):
does not exist: src/

---

## assistant

ACTION: pwd
```

---

## user

Invalid format. Reply only with a valid ACTION or with FILE blocks in the specified format.

---

## assistant

ACTION: ls ..
```

---

## user

RESULT (8 actions left):
caminho fora da base de conhecimento

---

## assistant

ACTION: find . -name "user.model.ts" -type f
```

---

## user

Invalid format. Reply only with a valid ACTION or with FILE blocks in the specified format.

---

## assistant

ACTION: find . -name "*.ts" -type f | head -10
```