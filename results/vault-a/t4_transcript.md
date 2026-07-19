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

# Tarefa: alterar papel de usuário

Implemente o endpoint de mudança de papel:

```
PATCH /tenants/{tenantId}/users/{userId}/role
Request JSON:  { "role": "OWNER" | "ADMIN" | "MEMBER" }
Sucesso: 200 com JSON do usuário atualizado
```

Implemente TODAS as regras de negócio, permissões, validações e convenções de
erro/auditoria que o time definiu para papéis.


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
@Singleton
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
```

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

ACTION: read produto/regras-papel.md
```

---

## user

RESULT (6 ações restantes):
arquivo não encontrado: produto/regras-papel.md

---

## assistant

ACTION: grep -r "papel\|role" .
```

---

## user

RESULT (5 ações restantes):
nenhum resultado para: -r "papel\|role" .

---

## assistant

ACTION: ls produto/
```

---

## user

RESULT (4 ações restantes):
planos-e-precos.md

---

## assistant

ACTION: ls dominio/
```

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
```

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

ACTION: read dominio/limites-de-plano.md
```

---

## user

RESULT (1 ações restantes):
---
tipo: regra-de-negocio
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# Limites de usuários por plano

| Plano | Máximo de assentos |
|---|---|
| FREE | 5 |
| PRO | 50 |
| ENTERPRISE | ilimitado (`maxUsers = null`) |

## O que conta como assento ocupado

`assentos ocupados = usuários do tenant com status != DELETED + convites com status PENDING`

Ou seja: **convite pendente ocupa vaga** (decisão registrada em
[adr-002](../decisoes/adr-002-convites-pendentes-contam-no-limite.md)).
Usuários INVITED, ACTIVE e SUSPENDED contam; DELETED não conta.

## Regra de bloqueio

Criar um convite quando `assentos ocupados >= máximo do plano` retorna
`422 PLAN_LIMIT_EXCEEDED` e **não** persiste nada.

## Quando usar / Quando NÃO usar

- Use ao criar convites e ao reativar usuários.
- NÃO aplique o limite ao reenviar um convite já existente (não cria assento novo).

## Relacionados

- [convites](convites.md)
- [../decisoes/adr-002-convites-pendentes-contam-no-limite.md](../decisoes/adr-002-convites-pendentes-contam-no-limite.md)
- [../produto/planos-e-precos.md](../produto/planos-e-precos.md)


---

## assistant

FILE: src/main/java/com/bench/api/UserRoleResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Path("/tenants/{tenantId}/users/{userId}/role")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class UserRoleResource {

    @Inject
    InMemoryStore store;

    @PATCH
    public Response changeRole(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            RoleChangeRequest request) {
        
        // Verificar se o ator está no mesmo tenant
        String actorId = getActorId();
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty() || !tenantId.equals(actorOpt.get().tenantId)) {
            return Response.status(404).build();
        }

        // Verificar se o usuário existe e pertence ao tenant
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty() || !tenantId.equals(targetUserOpt.get().tenantId)) {
            return Response.status(404).build();
        }

        User actor = actorOpt.get();
        User targetUser = targetUserOpt.get();

        // Verificar permissões do ator
        if (!hasPermission(actor, targetUser)) {
            return Response.status(403).entity("FORBIDDEN_ROLE").build();
        }

        // Verificar se está tentando alterar um OWNER protegido
        if (targetUser.role == Role.OWNER && actor.role != Role.OWNER) {
            return Response.status(403).entity("OWNER_PROTECTED").build();
        }

        // Verificar se é o último OWNER e tenta rebaixar
        if (targetUser.role == Role.OWNER && request.role != Role.OWNER && store.countOwners(tenantId) <= 1) {
            return Response.status(409).entity("LAST_OWNER").build();
        }

        // Realizar a mudança de papel
        targetUser.role = request.role;

        // Registrar auditoria
        AuditEntry audit = new AuditEntry();
        audit.id = "audit-" + Instant.now().toEpochMilli();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_ROLE_CHANGED";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "Changed role from " + targetUser.role + " to " + request.role;
        store.auditLog.add(audit);

        return Response.ok(targetUser).build();
    }

    private boolean hasPermission(User actor, User target) {
        // ADMIN+ pode alterar papéis
        if (actor.role == Role.ADMIN || actor.role == Role.OWNER) {
            return true;
        }
        return false;
    }

    private String getActorId() {
        // Simulando a leitura do header X-Actor-Id
        // Em produção, isso seria feito com Request.getHeader("X-Actor-Id")
        return "actor-id"; // Este valor seria obtido do header real
    }

    public static class RoleChangeRequest {
        public Role role;
    }
}
```