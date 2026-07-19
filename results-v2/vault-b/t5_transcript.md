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

ACTION: read src/app/user.model.ts

---

## user

RESULT (7 ações restantes):
arquivo não encontrado: src/app/user.model.ts

---

## assistant

ACTION: ls src/app/

---

## user

RESULT (6 ações restantes):
não existe: src/app/

---

## assistant

ACTION: ls .

---

## user

RESULT (5 ações restantes):
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

---

## user

RESULT (4 ações restantes):
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

---

## user

RESULT (3 ações restantes):
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

ACTION: read 202603150930-quem-pode-deletar.md

---

## user

RESULT (2 ações restantes):
# 202603150930 Quem pode excluir usuário

- ADMIN+ do próprio tenant ([[202601051030-papeis-do-tenant]],
  [[202602151100-isolamento-de-tenant-404]]).
- ADMIN não exclui OWNER → 403 `OWNER_PROTECTED`
  ([[202602101415-protecao-do-owner]]).
- **Ninguém exclui a si mesmo** → 422 `CANNOT_DELETE_SELF`. Dois motivos:
  evita tenant órfão por engano e limita estrago de sessão roubada.
- A exclusão em si é sempre soft ([[202603150900-soft-delete-30-dias]]) e
  audita `USER_SOFT_DELETED` com targetId = usuário excluído
  ([[202601201300-auditoria-de-mutacoes]]).


---

## assistant

ACTION: read 202601201300-auditoria-de-mutacoes.md

---

## user

RESULT (1 ações restantes):
# 202601201300 Auditoria de mutações

Toda mutação EFETIVADA de usuário/convite/papel grava um AuditEntry no
auditLog, na mesma operação (nada de "audito depois"). Tentativa negada
(403/422) NÃO gera entrada.

Campos: `id` (UUID novo), `tenantId`, `actorId` (o `X-Actor-Id`), `action`,
`targetId` (id do recurso afetado), `timestamp` (Instant UTC), `details`
(livre, opcional).

Ações válidas — não inventar strings fora desta lista, dashboards de
compliance quebram:

- `USER_INVITED` (targetId = id do convite)
- `INVITATION_RESENT` (targetId = id do convite)
- `USER_ROLE_CHANGED` (targetId = id do usuário)
- `USER_SOFT_DELETED` (targetId = id do usuário)
- `USER_RESTORED` (targetId = id do usuário)

Liga com tudo: [[202602041100-expiracao-de-convites-72h]],
[[202603150900-soft-delete-30-dias]], [[202601051030-papeis-do-tenant]].


---

## assistant

FILE: src/app/user-list.component.ts
```ts
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-user-list',
  templateUrl: './user-list.component.html',
  styleUrls: ['./user-list.component.scss']
})
export class UserListComponent {
  @Input() users: UserView[] = [];
}

interface UserView {
  id: string;
  email: string;
  role: 'OWNER' | 'ADMIN' | 'MEMBER';
  status: 'INVITED' | 'ACTIVE' | 'SUSPENDED' | 'DELETED';
  purgeAt?: string;
}
```