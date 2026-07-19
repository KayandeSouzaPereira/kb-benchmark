## system

Você é um engenheiro de software sênior de um time de produto.
Você NÃO tem acesso à documentação do time; use seu melhor julgamento para
regras de negócio e convenções.

Produza os arquivos finais neste formato exato (pode haver mais de um bloco
FILE):

FILE: caminho/relativo/do/Arquivo.java
```java
<conteúdo completo do arquivo>
```

Escreva arquivos completos e compiláveis; não modifique os arquivos
existentes do projeto.

---

## user

# Tarefa: listagem de usuários com badge de status (Angular)

Crie `src/app/user-list.component.ts`: componente standalone, selector
`app-user-list`, com `@Input() users: UserView[]` (importe de
`./user.model`).

Renderize uma tabela com e-mail, papel e status de cada usuário. O status
deve aparecer como **badge**, seguindo as convenções visuais e de texto que o
time definiu (classes CSS, rótulos exibidos e informações extras por status).
Use template inline.


## Projeto existente (Angular 18, standalone) — NÃO reescreva

Já existe `src/app/user.model.ts`:

```ts
export interface UserView {
  id: string;
  email: string;
  role: 'OWNER' | 'ADMIN' | 'MEMBER';
  status: 'INVITED' | 'ACTIVE' | 'SUSPENDED' | 'DELETED';
  purgeAt?: string;
}
```

Crie o componente em `src/app/user-list.component.ts` (template inline).


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
          <th>Papel</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr *ngFor="let user of users">
          <td>{{ user.email }}</td>
          <td>{{ user.role }}</td>
          <td>
            <span [class]="'badge badge-' + getUserStatusClass(user.status)"
                  [title]="getUserStatusTooltip(user.status, user.purgeAt)">
              {{ getUserStatusLabel(user.status) }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  `,
  standalone: true
})
export class UserListComponent {
  @Input() users: UserView[] = [];

  getUserStatusClass(status: UserView['status']): string {
    switch (status) {
      case 'ACTIVE':
        return 'success';
      case 'INVITED':
        return 'warning';
      case 'SUSPENDED':
        return 'danger';
      case 'DELETED':
        return 'secondary';
      default:
        return 'secondary';
    }
  }

  getUserStatusLabel(status: UserView['status']): string {
    switch (status) {
      case 'ACTIVE':
        return 'Ativo';
      case 'INVITED':
        return 'Convidado';
      case 'SUSPENDED':
        return 'Suspenso';
      case 'DELETED':
        return 'Excluído';
      default:
        return status;
    }
  }

  getUserStatusTooltip(status: UserView['status'], purgeAt?: string): string {
    switch (status) {
      case 'ACTIVE':
        return 'Usuário ativo no sistema';
      case 'INVITED':
        return 'Convite enviado, aguardando aceitação';
      case 'SUSPENDED':
        return 'Usuário suspenso temporariamente';
      case 'DELETED':
        if (purgeAt) {
          return `Usuário excluído. Será removido do sistema em ${purgeAt}`;
        }
        return 'Usuário excluído permanentemente';
      default:
        return '';
    }
  }
}
```