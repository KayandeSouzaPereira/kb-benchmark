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

ACTION: ls src/app/
```

---

## user

RESULT (13 actions left):
does not exist: src/app/

---

## assistant

ACTION: ls src/
```

---

## user

RESULT (12 actions left):
does not exist: src/

---

## assistant

ACTION: read user.model.ts
```

---

## user

RESULT (11 actions left):
file not found: user.model.ts

---

## assistant

ACTION: grep -r "UserView" . --include="*.ts"
```

---

## user

RESULT (10 actions left):
no results for: UserView" . --include="*.ts

---

## assistant

ACTION: grep -r "status.*badge" . --include="*.md"
```

---

## user

RESULT (9 actions left):
no results for: status.*badge" . --include="*.md

---

## assistant

ACTION: grep -r "badge" . --include="*.md"
```

---

## user

RESULT (8 actions left):
no results for: badge" . --include="*.md

---

## assistant

ACTION: grep -r "status" . --include="*.md"
```

---

## user

RESULT (7 actions left):
no results for: status" . --include="*.md

---

## assistant

ACTION: ls .
```

---

## user

RESULT (6 actions left):
INDEX.md
billing/
code-standards/
decisions/
domain/
notifications/
product/
rate-limiting/
runbooks/
sso/
webhooks/

---

## assistant

ACTION: grep -r "status.*badge\|badge.*status" . --include="*.md"
```

---

## user

RESULT (5 actions left):
no results for: status.*badge\|badge.*status" . --include="*.md

---

## assistant

ACTION: read product/README.md
```

---

## user

RESULT (4 actions left):
file not found: product/README.md

---

## assistant

ACTION: read INDEX.md
```

---

## user

RESULT (3 actions left):
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


---

## assistant

ACTION: read code-standards/frontend-status-badges.md
```

---

## user

RESULT (2 actions left):
---
type: technical-convention
system: user-management
status: active
updated: 2026-04-11
---

# User status badges in the frontend

Everywhere a user status is displayed we use a badge with a **standardized CSS
class and pt-BR label**. Never show the raw enum (`ACTIVE` etc.) to the user.

The product UI is in Brazilian Portuguese — the labels below are the exact
strings and must not be translated:

| Status | CSS class | Displayed label |
|---|---|---|
| `ACTIVE` | `badge-success` | Ativo |
| `INVITED` | `badge-warning` | Convite pendente |
| `SUSPENDED` | `badge-muted` | Suspenso |
| `DELETED` | `badge-danger` | Excluído |

## Extra rule for DELETED

A deleted user shows, next to the badge, the definitive removal date:
`Remoção definitiva em {purgeAt}` formatted as **dd/MM/yyyy**
(in Angular: `{{ user.purgeAt | date:'dd/MM/yyyy' }}`).

## When to use / When NOT to use

- Use in every user list, card or detail view.
- Do NOT create per-screen color/text variations; the table above is canonical.

## Related

- [../domain/user-deletion.md](../domain/user-deletion.md)


---

## assistant

FILE: src/app/user-list.component.ts
```typescript
import { Component, Input } from '@angular/core';
import { UserView } from './user.model';

@Component({
  selector: 'app-user-list',
  template: `
    <table class="table">
      <thead>
        <tr>
          <th>Email</th>
          <th>Role</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr *ngFor="let user of users">
          <td>{{ user.email }}</td>
          <td>{{ user.role }}</td>
          <td>
            <span [class]="getStatusBadgeClass(user.status)" class="badge">
              {{ getStatusLabel(user.status) }}
            </span>
            <span *ngIf="user.status === 'DELETED' && user.purgeAt">
              <br>
              Remoção definitiva em {{ user.purgeAt | date:'dd/MM/yyyy' }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  `,
  standalone: true
})
export class UserListComponent {
  @Input() users!: UserView[];

  getStatusBadgeClass(status: UserView['status']): string {
    switch (status) {
      case 'ACTIVE': return 'badge-success';
      case 'INVITED': return 'badge-warning';
      case 'SUSPENDED': return 'badge-muted';
      case 'DELETED': return 'badge-danger';
      default: return '';
    }
  }

  getStatusLabel(status: UserView['status']): string {
    switch (status) {
      case 'ACTIVE': return 'Ativo';
      case 'INVITED': return 'Convite pendente';
      case 'SUSPENDED': return 'Suspenso';
      case 'DELETED': return 'Excluído';
      default: return '';
    }
  }
}
```