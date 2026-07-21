## system

You are a senior software engineer on a product team.
You do NOT have access to the team's documentation; use your best judgment for
business rules and conventions.

Produce the final files in this exact format (there may be more than one FILE
block):

FILE: relative/path/to/File.java
```java
<complete file content>
```

Write complete, compilable files; do not modify the project's existing
files.

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

FILE: src/app/user-list.component.ts
```typescript
import { Component, Input } from '@angular/core';
import { UserView } from './user.model';

@Component({
  selector: 'app-user-list',
  template: `
    <table class="user-table">
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
            <span [class]="'badge badge-' + user.status.toLowerCase()">
              {{ getStatusLabel(user.status) }}
            </span>
            <ng-container *ngIf="user.purgeAt && user.status === 'SUSPENDED'">
              <br>
              <small>Purges at: {{ user.purgeAt }}</small>
            </ng-container>
          </td>
        </tr>
      </tbody>
    </table>
  `,
  styles: [`
    .user-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }
    
    .user-table th,
    .user-table td {
      padding: 0.75rem;
      text-align: left;
      border-bottom: 1px solid #dee2e6;
    }
    
    .user-table th {
      background-color: #f8f9fa;
      font-weight: 600;
    }
    
    .badge {
      padding: 0.25rem 0.5rem;
      border-radius: 0.375rem;
      font-size: 0.75rem;
      font-weight: 500;
      text-transform: uppercase;
    }
    
    .badge-invited {
      background-color: #e9ecef;
      color: #495057;
    }
    
    .badge-active {
      background-color: #d4edda;
      color: #155724;
    }
    
    .badge-suspended {
      background-color: #fff3cd;
      color: #856404;
    }
    
    .badge-deleted {
      background-color: #f8d7da;
      color: #721c24;
    }
  `]
})
export class UserListComponent {
  @Input() users: UserView[] = [];

  getStatusLabel(status: UserView['status']): string {
    switch (status) {
      case 'INVITED': return 'Invited';
      case 'ACTIVE': return 'Active';
      case 'SUSPENDED': return 'Suspended';
      case 'DELETED': return 'Deleted';
      default: return status;
    }
  }
}
```