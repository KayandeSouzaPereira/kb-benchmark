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
        <span [class]="'badge badge-' + user.status.toLowerCase()" 
              [title]="user.status === 'DELETED' ? 'Usuário excluído' : user.status === 'SUSPENDED' ? 'Usuário suspenso' : ''">
          {{ user.status }}
        </span>
      </td>
    </tr>
  </tbody>
</table>
```

FILE: src/app/user-list.component.css
```css
.badge {
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  text-transform: uppercase;
}

.badge-invited {
  background-color: #ffd580;
  color: #c87000;
}

.badge-active {
  background-color: #a3e635;
  color: #00695c;
}

.badge-suspended {
  background-color: #f48024;
  color: #fff;
}

.badge-deleted {
  background-color: #d32f2f;
  color: #fff;
}
```