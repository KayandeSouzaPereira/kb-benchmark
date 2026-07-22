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

ACTION: ls .
```

---

## user

RESULT (8 actions left):
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

RESULT (7 actions left):
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

ACTION: read 202603150900-soft-delete-30-days.md
```

---

## user

RESULT (6 actions left):
# 202603150900 Soft-delete with purge in 30 days

There is no hard delete of users in the product. Deleting =

- `status = DELETED`
- `deletedAt = now`
- `purgeAt = now + 30 days` (the definitive purge job reads this field)
- the record STAYS in the store

Success responds 204 No Content. Restoring within the window is allowed
(audit action `USER_RESTORED`).

30 days was the agreement with legal: compliance wants a minimum 30-day trail,
LGPD killed the 90-day idea. I considered a boolean `deleted` flag and
discarded it — without `purgeAt` the purge job cannot work.

Who can delete: [[202603150930-who-can-delete-users]].
Deletion auditing: [[202601201300-mutation-audit-log]].


---

## assistant

ACTION: read 202603150930-who-can-delete-users.md
```

---

## user

RESULT (5 actions left):
# 202603150930 Who can delete a user

- ADMIN+ of the same tenant ([[202601051030-tenant-roles]],
  [[202602151100-tenant-isolation-404]]).
- An ADMIN does not delete an OWNER → 403 `OWNER_PROTECTED`
  ([[202602101415-owner-protection]]).
- **Nobody deletes themselves** → 422 `CANNOT_DELETE_SELF`. Two reasons:
  prevents accidental orphan tenants and limits stolen-session damage.
- Deletion itself is always soft ([[202603150900-soft-delete-30-days]]) and
  audits `USER_SOFT_DELETED` with targetId = the deleted user
  ([[202601201300-mutation-audit-log]]).


---

## assistant

ACTION: read 202601051030-tenant-roles.md
```

---

## user

RESULT (4 actions left):
# 202601051030 Tenant roles

Three roles, strict hierarchy: OWNER > ADMIN > MEMBER.

Administrative mutations — inviting someone, deleting a user, changing a role —
require ADMIN or OWNER ("ADMIN+"). A MEMBER who tries gets 403 with code
`FORBIDDEN_ROLE` (codes in [[202601201330-api-error-codes]]).

But hierarchy is not just "whoever is above rules": the owner has specific
protections that an admin cannot cross → [[202602101415-owner-protection]].

And the actor must belong to the tenant itself → [[202602151100-tenant-isolation-404]].


---

## assistant

ACTION: read 202602101415-owner-protection.md
```

---

## user

RESULT (3 actions left):
# 202602101415 Owner protection

Realized today while discussing the Vetrix customer incident: if an ADMIN can
demote or delete an OWNER, a malicious admin takes over the tenant.

Rule we settled on: **an ADMIN never modifies nor deletes an OWNER** — neither
role nor deletion. Response: 403 `OWNER_PROTECTED`. Only an OWNER touches
another OWNER, and only an OWNER promotes someone to OWNER.

This connects to the last-owner edge case: [[202602101430-last-owner]].
Roles in general: [[202601051030-tenant-roles]].


---

## assistant

ACTION: read 202602101430-last-owner.md
```

---

## user

RESULT (2 actions left):
# 202602101430 Last owner

Continuation of [[202602101415-owner-protection]]: a tenant can never be left
without an OWNER.

Any operation that would leave zero active owners — demoting the last owner
(including demoting themselves), removing them, them leaving the tenant —
fails with **409 `LAST_OWNER`**.

With two or more owners the operation goes through: one owner may demote the
other normally.

"Active owner" here = owner with status != DELETED. Relates to
[[202603150900-soft-delete-30-days]].


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
          <th>E-mail</th>
          <th>Role</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr *ngFor="let user of users">
          <td>{{ user.email }}</td>
          <td>{{ user.role }}</td>
          <td>
            <span [class]="getStatusBadgeClass(user.status)" 
                  [title]="getStatusTooltip(user)">
              {{ getStatusLabel(user.status) }}
            </span>
            <ng-container *ngIf="user.status === 'DELETED'">
              <br>
              <small>Remoção definitiva em {{ user.purgeAt | date:'dd/MM/yyyy' }}</small>
            </ng-container>
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

  getStatusTooltip(user: UserView): string {
    if (user.status === 'DELETED' && user.purgeAt) {
      return `Remoção definitiva em ${new Date(user.purgeAt).toLocaleDateString('pt-BR')}`;
    }
    return '';
  }
}
```