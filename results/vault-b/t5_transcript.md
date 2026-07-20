## system

Você é um engenheiro de software sênior de um time de produto.
O time mantém uma base de conhecimento em arquivos Markdown com as regras de
negócio e convenções. Você DEVE consultá-la antes de escrever código, porque
as regras específicas do produto não são óbvias.

Para explorar a base, responda com UMA única linha de comando por mensagem:

ACTION: ls <caminho>      (lista arquivos de um diretório; use "." para a raiz)
ACTION: grep <termo>      (busca textual em todas as notas)
ACTION: read <arquivo>    (lê o conteúdo de uma nota)

Após cada ACTION você receberá o resultado. Você tem no máximo 8
ações no total — use-as bem.

Quando tiver o que precisa, produza os arquivos finais neste formato exato
(pode haver mais de um bloco FILE):

FILE: caminho/relativo/do/Arquivo.java
```java
<conteúdo completo do arquivo>
```

Regras do formato: nunca misture ACTION e FILE na mesma resposta; escreva
arquivos completos e compiláveis; não modifique os arquivos existentes do
projeto.

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

ACTION: ls .
```

---

## user

RESULT (7 ações restantes):
202601050900-mapa-dominio-usuarios.md
202601051030-papeis-do-tenant.md
202601080800-lockout-e-senhas.md
202601121000-limites-por-plano.md
202601201300-auditoria-de-mutacoes.md
202601201330-codigos-de-erro-da-api.md
202602041100-expiracao-de-convites-72h.md
202602041130-reenvio-de-convites.md
202602101415-protecao-do-owner.md
202602101430-ultimo-owner.md
202602151100-isolamento-de-tenant-404.md
202603121015-convites-e-limite-duvida.md
202603150900-soft-delete-30-dias.md
202603150930-quem-pode-deletar.md
202604010900-mapa-api-e-convencoes.md
202604111600-badges-de-status-no-front.md
202605021430-convites-pendentes-contam.md
202605190800-ideias-de-precos.md

---

## assistant

ACTION: read 202604111600-badges-de-status-no-front.md
```

---

## user

RESULT (6 ações restantes):
# 202604111600 Badges de status no front

Nunca mostrar o enum cru para o usuário. Mapeamento canônico
(classe CSS + rótulo PT-BR):

- ACTIVE → `badge-success` / "Ativo"
- INVITED → `badge-warning` / "Convite pendente"
- SUSPENDED → `badge-muted` / "Suspenso"
- DELETED → `badge-danger` / "Excluído"

Para DELETED, mostrar junto a data de remoção definitiva:
"Remoção definitiva em {purgeAt}" no formato dd/MM/yyyy
(Angular: `{{ user.purgeAt | date:'dd/MM/yyyy' }}`).
O purgeAt vem do soft-delete: [[202603150900-soft-delete-30-dias]].

Nada de variação de cor por tela — já tivemos 3 verdes diferentes.


---

## assistant

ACTION: read 202603150900-soft-delete-30-dias.md
```

---

## user

RESULT (5 ações restantes):
# 202603150900 Soft-delete com purge em 30 dias

Não existe hard delete de usuário no produto. Excluir =

- `status = DELETED`
- `deletedAt = agora`
- `purgeAt = agora + 30 dias` (o job de purge definitivo lê esse campo)
- o registro CONTINUA no store

Sucesso responde 204 No Content. Restaurar dentro da janela é permitido
(ação de auditoria `USER_RESTORED`).

30 dias foi acordo com jurídico: compliance pede trilha mínima de 30,
LGPD derrubou a ideia de 90. Cogitei flag booleana `deleted` e descartei —
sem `purgeAt` o job de purge não funciona.

Quem pode excluir: [[202603150930-quem-pode-deletar]].
Auditoria da exclusão: [[202601201300-auditoria-de-mutacoes]].


---

## assistant

ACTION: read 202601050900-mapa-dominio-usuarios.md
```

---

## user

RESULT (4 ações restantes):
# 202601050900 Mapa — domínio de gestão de usuários

Nota-índice do que já pensei sobre o domínio de usuários do produto.

- Papéis e hierarquia: [[202601051030-papeis-do-tenant]]
- Proteções especiais do owner: [[202602101415-protecao-do-owner]] e [[202602101430-ultimo-owner]]
- Isolamento entre tenants: [[202602151100-isolamento-de-tenant-404]]
- Limites de assentos: [[202601121000-limites-por-plano]] (atenção à correção em [[202605021430-convites-pendentes-contam]])
- Convites: [[202602041100-expiracao-de-convites-72h]], [[202602041130-reenvio-de-convites]]
- Exclusão: [[202603150900-soft-delete-30-dias]], [[202603150930-quem-pode-deletar]]
- Auditoria: [[202601201300-auditoria-de-mutacoes]]
- Autenticação (separado do domínio de gestão): [[202601080800-lockout-e-senhas]]

Convenções de código ficam em outro mapa: [[202604010900-mapa-api-e-convencoes]].


---

## assistant

ACTION: grep "badge" 202604111600-badges-de-status-no-front.md
```

---

## user

RESULT (3 ações restantes):
nenhum resultado para: badge" 202604111600-badges-de-status-no-front.md

---

## assistant

ACTION: grep -i "badge" 202604111600-badges-de-status-no-front.md
```

---

## user

RESULT (2 ações restantes):
nenhum resultado para: -i "badge" 202604111600-badges-de-status-no-front.md

---

## assistant

ACTION: read 202605190800-ideias-de-precos.md
```

---

## user

RESULT (1 ações restantes):
# 202605190800 Ideias de preços (rascunho)

FREE R$ 0 (5 assentos) / PRO R$ 49 por usuário/mês (50) / ENTERPRISE sob
consulta (ilimitado).

Pensando se PRO não deveria ter tier anual com desconto de 20%. Downgrade
exige caber no limite do plano de destino
([[202601121000-limites-por-plano]]).

Ainda rascunho — nada disso virou decisão.


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
            <span [class]="getStatusClass(user.status)" [title]="getStatusTooltip(user)">
              {{ getStatusLabel(user.status) }}
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

  getStatusClass(status: UserView['status']): string {
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

  getStatusTooltip(user: UserView): string {
    if (user.status === 'DELETED' && user.purgeAt) {
      return `Remoção definitiva em ${user.purgeAt}`;
    }
    return '';
  }
}
```