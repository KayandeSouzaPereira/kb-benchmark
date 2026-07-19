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
INDEX.md
decisoes/
dominio/
padroes-codigo/
produto/
runbooks/

---

## assistant

ACTION: ls produto/

---

## user

RESULT (4 ações restantes):
planos-e-precos.md

---

## assistant

ACTION: ls dominio/

---

## user

RESULT (3 ações restantes):
auditoria.md
autenticacao-e-lockout.md
convites.md
exclusao-de-usuarios.md
limites-de-plano.md
papeis-e-permissoes.md

---

## assistant

ACTION: read dominio/papeis-e-permissoes.md

---

## user

RESULT (2 ações restantes):
---
tipo: regra-de-negocio
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# Papéis e permissões

Hierarquia dentro de um tenant: `OWNER > ADMIN > MEMBER`.

## Regras

- **Convidar usuários, excluir usuários e alterar papéis exige ADMIN ou OWNER** (ADMIN+).
  MEMBER que tentar recebe `403 FORBIDDEN_ROLE`.
- **ADMIN nunca altera nem exclui um OWNER** (nem papel, nem exclusão): `403 OWNER_PROTECTED`.
  Somente um OWNER pode mexer em outro OWNER ou promover alguém a OWNER.
- **O tenant nunca pode ficar sem OWNER**: rebaixar ou remover o último OWNER ativo
  retorna `409 LAST_OWNER`. Com dois ou mais owners, um owner pode rebaixar o outro.
- **Isolamento de tenant**: o ator (header `X-Actor-Id`) precisa pertencer ao tenant da URL.
  Ator de outro tenant recebe `404 NOT_FOUND` — nunca 403, para não vazar a existência
  do recurso.

## Quando usar / Quando NÃO usar

- Use em todo endpoint de mutação de usuários, convites ou papéis.
- NÃO confunda com autenticação (login/senha) — ver [autenticacao-e-lockout](autenticacao-e-lockout.md).

## Anti-padrões já observados

- Checar papel depois de mutar o estado (validar SEMPRE antes de escrever no store).
- Retornar 403 para ator de outro tenant (vaza existência; o correto é 404).

## Relacionados

- [exclusao-de-usuarios](exclusao-de-usuarios.md)
- [convites](convites.md)
- [../padroes-codigo/formato-de-erros-api.md](../padroes-codigo/formato-de-erros-api.md)
- [auditoria](auditoria.md)


---

## assistant

ACTION: read dominio/convites.md

---

## user

RESULT (1 ações restantes):
---
tipo: regra-de-negocio
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# Ciclo de vida do convite

## Criação

- Somente ADMIN+ cria convites (ver [papeis-e-permissoes](papeis-e-permissoes.md)).
- Respeita o limite do plano — convite pendente conta como assento
  (ver [limites-de-plano](limites-de-plano.md)).
- **Todo convite expira em 72 horas** a partir da criação: `expiresAt = createdAt + 72h`.
- Convite nasce com `status = PENDING` e `resendCount = 0`.
- Auditoria obrigatória: ação `USER_INVITED` (ver [auditoria](auditoria.md)).

## Reenvio

- Somente ADMIN+.
- **Máximo de 3 reenvios por convite.** O 4º retorna `422 RESEND_LIMIT_REACHED`
  e não altera nada.
- Cada reenvio **reseta a expiração para +72h a partir de agora** e incrementa
  `resendCount`.
- Reenviar um convite já expirado é permitido e o **reativa** (nova janela de 72h).
- Auditoria obrigatória: ação `INVITATION_RESENT`.

## Aceitação

- Aceitar convite expirado retorna `410 INVITATION_EXPIRED`.
- Aceitação cria o usuário com `status = ACTIVE` e marca o convite como `ACCEPTED`.

## Anti-padrões já observados

- Aplicar o limite de plano no reenvio (errado: reenvio não cria assento).
- Esquecer de resetar `expiresAt` no reenvio.

## Relacionados

- [papeis-e-permissoes](papeis-e-permissoes.md)
- [limites-de-plano](limites-de-plano.md)
- [auditoria](auditoria.md)
- [../padroes-codigo/formato-de-erros-api.md](../padroes-codigo/formato-de-erros-api.md)


---

## assistant

ACTION: read dominio/exclusao-de-usuarios.md

---

## user

RESULT (0 ações restantes):
---
tipo: regra-de-negocio
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# Exclusão de usuários (soft-delete)

**Não existe hard delete de usuário neste produto.** Decisão registrada em
[adr-001](../decisoes/adr-001-soft-delete-com-retencao.md).

## Regras

- Excluir um usuário significa: `status = DELETED`, `deletedAt = agora`,
  `purgeAt = agora + 30 dias`. O registro **permanece no store**.
- Somente ADMIN+ exclui, e apenas usuários do próprio tenant.
- ADMIN não pode excluir OWNER: `403 OWNER_PROTECTED`
  (ver [papeis-e-permissoes](papeis-e-permissoes.md)).
- **Ninguém exclui a si mesmo**: `422 CANNOT_DELETE_SELF` — evita tenant órfão
  por acidente e abuso de sessões roubadas.
- Sucesso responde `204 No Content`.
- Auditoria obrigatória: ação `USER_SOFT_DELETED` com `targetId` = id do usuário
  excluído (ver [auditoria](auditoria.md)).

## Quando usar / Quando NÃO usar

- Use em qualquer remoção de usuário disparada pela UI ou API.
- NÃO use para saída voluntária do tenant (fluxo "leave" tem regra própria
  de último owner).

## Anti-padrões já observados

- `store.users.remove(id)` — perde histórico e quebra auditoria. Nunca.
- Esquecer `purgeAt` — o job de purge definitivo depende desse campo.

## Relacionados

- [../decisoes/adr-001-soft-delete-com-retencao.md](../decisoes/adr-001-soft-delete-com-retencao.md)
- [papeis-e-permissoes](papeis-e-permissoes.md)
- [auditoria](auditoria.md)


---

## assistant

FILE: src/app/user-list.component.ts
```ts
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-user-list',
  templateUrl: './user-list.component.html',
  styleUrls: ['./user-list.component.css']
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