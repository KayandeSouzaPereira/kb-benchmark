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
```ts
import { Component, Input } from '@angular/core';

import { UserView } from './user.model';

@Component({
  selector: 'app-user-list',
  templateUrl: './user-list.component.html',
  styleUrls: ['./user-list.component.css']
})
export class UserListComponent {
  @Input() users: UserView[] = [];
}

```

FILE: src/app/user-list.component.html
```html
<table>
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
        <span [class]="getStatusClass(user.status)" [title]="getStatusTooltip(user.status)">
          {{ user.status }}
        </span>
      </td>
    </tr>
  </tbody>
</table>
```

FILE: src/app/user-list.component.css
```css
/* Estilos para badge de status */
.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.INVITED {
  background-color: #f0f0f0;
  color: #555;
}

.status-badge.ACTIVE {
  background-color: #d4edda;
  color: #155724;
}

.status-badge.SUSPENDED {
  background-color: #f8d7da;
  color: #721c24;
}

.status-badge.DELETED {
  background-color: #f5f5f5;
  color: #868e96;
}
```