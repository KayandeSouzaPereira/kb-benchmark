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

ACTION: read src/app/user.model.ts
```

---

## user

RESULT (10 actions left):
file not found: src/app/user.model.ts

---

## assistant

ACTION: grep -r "UserView" .
```

---

## user

RESULT (9 actions left):
no results for: UserView

---

## assistant

ACTION: grep -r "status.*badge" .
```

---

## user

RESULT (8 actions left):
no results for: status.*badge

---

## assistant

ACTION: grep -r "badge" .
```

---

## user

RESULT (7 actions left):
202604010900-api-and-conventions-map.md:7: - Frontend status badges: [[202604111600-frontend-status-badges]]
202604111600-frontend-status-badges.md:1: # 202604111600 Frontend status badges
202604111600-frontend-status-badges.md:7: - ACTIVE → `badge-success` / "Ativo"
202604111600-frontend-status-badges.md:8: - INVITED → `badge-warning` / "Convite pendente"
202604111600-frontend-status-badges.md:9: - SUSPENDED → `badge-muted` / "Suspenso"
202604111600-frontend-status-badges.md:10: - DELETED → `badge-danger` / "Excluído"

---

## assistant

ACTION: read 202604111600-frontend-status-badges.md
```

---

## user

RESULT (6 actions left):
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

RESULT (5 actions left):
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

ACTION: read 202604010900-api-and-conventions-map.md
```

---

## user

RESULT (4 actions left):
# 202604010900 Map — API and team conventions

Index note for the technical conventions we've settled on.

- HTTP error format and codes: [[202601201330-api-error-codes]]
- Mandatory audit on mutations: [[202601201300-mutation-audit-log]]
- Frontend status badges: [[202604111600-frontend-status-badges]]

See also the domain map: [[202601050900-user-domain-map]].


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
          <th>Função</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr *ngFor="let user of users">
          <td>{{ user.email }}</td>
          <td>{{ user.role }}</td>
          <td>
            <span [class]="getBadgeClass(user.status)" 
                  [title]="getStatusTitle(user)">
              {{ getStatusLabel(user.status) }}
            </span>
            <ng-container *ngIf="user.status === 'DELETED' && user.purgeAt">
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

  getBadgeClass(status: UserView['status']): string {
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
      default: return status;
    }
  }

  getStatusTitle(user: UserView): string {
    if (user.status === 'DELETED' && user.purgeAt) {
      return `Remoção definitiva em ${new Date(user.purgeAt).toLocaleDateString('pt-BR')}`;
    }
    return '';
  }
}
```