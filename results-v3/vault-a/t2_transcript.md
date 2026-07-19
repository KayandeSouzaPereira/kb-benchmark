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

# Tarefa: excluir usuário

Implemente o endpoint de exclusão de usuário:

```
DELETE /tenants/{tenantId}/users/{userId}
Sucesso: 204 No Content
```

Implemente TODAS as regras de negócio, permissões, validações e convenções de
erro/auditoria que o time definiu para exclusão de usuários.


## Projeto existente (Quarkus 3, Java 21) — NÃO reescreva estas classes

Pacote `com.bench.model`:

```java
public enum Role { OWNER, ADMIN, MEMBER }
public enum UserStatus { INVITED, ACTIVE, SUSPENDED, DELETED }
public enum Plan { FREE, PRO, ENTERPRISE }        // campo público: Integer maxUsers (null = ilimitado)
public enum InvitationStatus { PENDING, ACCEPTED, REVOKED }

public class User { public String id, tenantId, email; public Role role;
                    public UserStatus status; public java.time.Instant deletedAt, purgeAt; }
public class Tenant { public String id, name; public Plan plan; }
public class Invitation { public String id, tenantId, email; public Role role;
                          public java.time.Instant createdAt, expiresAt;
                          public int resendCount; public InvitationStatus status; }
public class AuditEntry { public String id, tenantId, actorId, action, targetId;
                          public java.time.Instant timestamp; public String details; }
```

Pacote `com.bench.store` — injete com `@Inject`:

```java
@ApplicationScoped
public class InMemoryStore {
    public final Map<String, Tenant> tenants;
    public final Map<String, User> users;
    public final Map<String, Invitation> invitations;
    public final List<AuditEntry> auditLog;
    public Optional<User> findUser(String id);
    public List<User> usersOfTenant(String tenantId);
    public List<Invitation> invitationsOfTenant(String tenantId);
    public long countOwners(String tenantId);   // owners com status != DELETED
    public void reset();
}
```

Contexto de autenticação: o id do usuário autenticado (ator) chega no header
HTTP `X-Actor-Id` e corresponde a um `User` no store.

Crie seus recursos REST (jakarta.ws.rs) em `src/main/java/com/bench/api/`.
Lembre-se dos imports: `com.bench.model.*`, `com.bench.store.InMemoryStore`,
`jakarta.ws.rs.*`, `jakarta.ws.rs.core.*`, `jakarta.inject.Inject`. Use apenas
classes e métodos que existem no scaffold acima.

Armadilhas de API conhecidas:
- Para status HTTP fora do enum padrão (ex.: 422, 410), use
  `Response.status(422)` — `Response.Status` NÃO tem essas constantes.
- `Instant` não tem `plusHours`/`plusDays`; use
  `instant.plus(java.time.Duration.ofHours(n))`.


---

## assistant

ACTION: ls .

---

## user

RESULT (7 ações restantes):
INDEX.md
decisoes/
dominio/
padroes-codigo/
produto/
runbooks/

---

## assistant

ACTION: ls produto

---

## user

RESULT (6 ações restantes):
planos-e-precos.md

---

## assistant

ACTION: read produto/planos-e-precos.md

---

## user

RESULT (5 ações restantes):
---
tipo: produto
sistema: gestao-usuarios
status: ativo
atualizado: 2026-06-01
---

# Planos e preços

| Plano | Preço | Assentos | Suporte |
|---|---|---|---|
| FREE | R$ 0 | 5 | comunidade |
| PRO | R$ 49/usuário/mês | 50 | e-mail 24h |
| ENTERPRISE | sob consulta | ilimitado | CSM dedicado + SLA |

Upgrade é self-service; downgrade exige que o tenant esteja dentro do limite
do plano de destino. Detalhes técnicos do limite:
[limites-de-plano](../dominio/limites-de-plano.md).


---

## assistant

ACTION: ls dominio

---

## user

RESULT (4 ações restantes):
auditoria.md
autenticacao-e-lockout.md
convites.md
exclusao-de-usuarios.md
limites-de-plano.md
papeis-e-permissoes.md

---

## assistant

ACTION: read exclusao-de-usuarios.md

---

## user

RESULT (3 ações restantes):
arquivo não encontrado: exclusao-de-usuarios.md

---

## assistant

ACTION: ls dominio

---

## user

RESULT (2 ações restantes):
auditoria.md
autenticacao-e-lockout.md
convites.md
exclusao-de-usuarios.md
limites-de-plano.md
papeis-e-permissoes.md

---

## assistant

ACTION: read dominio/exclusao-de-usuarios.md

---

## user

RESULT (1 ações restantes):
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

ACTION: read dominio/papeis-e-permissoes.md

---

## user

RESULT (0 ações restantes):
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

FILE: src/main/java/com/bench/api/UserResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;

import java.time.Instant;
import java.time.Duration;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {
    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(@PathParam("tenantId") String tenantId,
                              @PathParam("userId") String userId,
                              @HeaderParam("X-Actor-Id") String actorId) {
        // Verificar se o ator pertence ao tenant
        if (!store.usersOfTenant(tenantId).stream()
                .anyMatch(user -> user.id.equals(actorId))) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Buscar usuário
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User user = userOpt.get();
        if (!tenantId.equals(user.tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Verificar permissões
        if (user.status == UserStatus.DELETED) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        if (actorId.equals(userId)) {
            return Response.status(422).entity("CANNOT_DELETE_SELF").build();
        }

        if (user.role == Role.OWNER) {
            return Response.status(403).entity("OWNER_PROTECTED").build();
        }

        // Verificar se o ator tem permissão para excluir
        if (user.role == Role.MEMBER) {
            return Response.status(403).entity("FORBIDDEN_ROLE").build();
        }

        // Atualizar status do usuário
        user.status = UserStatus.DELETED;
        user.deletedAt = Instant.now();
        user.purgeAt = Instant.now().plus(Duration.ofDays(30));

        // Auditoria
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_SOFT_DELETED";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "User deleted by " + actorId;

        store.auditLog.add(audit);

        return Response.noContent().build();
    }
}
```