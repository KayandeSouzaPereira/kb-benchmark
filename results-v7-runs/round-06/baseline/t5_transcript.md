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
            <span *ngIf="user.purgeAt" class="purge-info">
              (purges {{ user.purgeAt }})
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  `,
  styles: [`
    .user-table {
      width: 100%;
      border-collapse: collapse;
    }
    
    .user-table th,
    .user-table td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }
    
    .user-table th {
      background-color: #f5f5f5;
      font-weight: bold;
    }
    
    .badge {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 0.8em;
      font-weight: bold;
      vertical-align: middle;
    }
    
    .badge-invited {
      background-color: #e3f2fd;
      color: #1976d2;
    }
    
    .badge-active {
      background-color: #e8f5e9;
      color: #388e3c;
    }
    
    .badge-suspended {
      background-color: #fff3e0;
      color: #f57c00;
    }
    
    .badge-deleted {
      background-color: #ffebee;
      color: #d32f2f;
    }
    
    .purge-info {
      margin-left: 8px;
      font-size: 0.8em;
      color: #666;
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