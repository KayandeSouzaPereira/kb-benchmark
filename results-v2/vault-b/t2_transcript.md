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


---

## assistant

ACTION: ls .

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

ACTION: grep 'excluir usuário'

---

## user

RESULT (6 ações restantes):
202601051030-papeis-do-tenant.md:5: Mutações administrativas — convidar alguém, excluir usuário, mudar papel —
202603150930-quem-pode-deletar.md:1: # 202603150930 Quem pode excluir usuário

---

## assistant

ACTION: read 202601051030-papeis-do-tenant.md

---

## user

RESULT (5 ações restantes):
# 202601051030 Papéis do tenant

Três papéis, hierarquia estrita: OWNER > ADMIN > MEMBER.

Mutações administrativas — convidar alguém, excluir usuário, mudar papel —
pedem ADMIN ou OWNER ("ADMIN+"). Um MEMBER que tente recebe 403 com código
`FORBIDDEN_ROLE` (códigos em [[202601201330-codigos-de-erro-da-api]]).

Mas hierarquia não é só "quem está acima manda": o owner tem proteções
específicas que um admin não atravessa → [[202602101415-protecao-do-owner]].

E o ator precisa ser do próprio tenant → [[202602151100-isolamento-de-tenant-404]].


---

## assistant

ACTION: read 202603150930-quem-pode-deletar.md

---

## user

RESULT (4 ações restantes):
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

ACTION: read 202601201300-auditoria-de-mutacoes.md

---

## user

RESULT (2 ações restantes):
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

ACTION: read 202601201330-codigos-de-erro-da-api.md

---

## user

RESULT (1 ações restantes):
# 202601201330 Códigos de erro da API

Envelope padrão de erro de negócio (o `code` é contrato estável, `message`
é livre):

```json
{ "code": "CODIGO_ESTAVEL", "message": "texto humano" }
```

Códigos que já firmamos:

- 403 `FORBIDDEN_ROLE` — papel insuficiente ([[202601051030-papeis-do-tenant]])
- 403 `OWNER_PROTECTED` — admin mexendo em owner ([[202602101415-protecao-do-owner]])
- 409 `LAST_OWNER` — tenant ficaria sem owner ([[202602101430-ultimo-owner]])
- 422 `PLAN_LIMIT_EXCEEDED` — limite de assentos ([[202605021430-convites-pendentes-contam]])
- 422 `CANNOT_DELETE_SELF` — auto-exclusão ([[202603150930-quem-pode-deletar]])
- 422 `RESEND_LIMIT_REACHED` — 4º reenvio ([[202602041130-reenvio-de-convites]])
- 410 `INVITATION_EXPIRED` — aceitar convite vencido ([[202602041100-expiracao-de-convites-72h]])
- 404 `NOT_FOUND` — inexistente OU ator de outro tenant ([[202602151100-isolamento-de-tenant-404]])

Sem stacktrace no body, nunca.


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
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(@PathParam("tenantId") String tenantId, 
                              @PathParam("userId") String userId, 
                              @HeaderParam("X-Actor-Id") String actorId) {
        // Verificar se o usuário existe
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User user = userOpt.get();
        
        // Verificar se o ator é do mesmo tenant
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Verificar se o ator está tentando excluir a si mesmo
        if (actorId.equals(userId)) {
            return Response.status(Response.Status.UNPROCESSABLE_ENTITY)
                          .entity(new JsonObject().put("code", "CANNOT_DELETE_SELF")
                                                  .put("message", "Cannot delete yourself"))
                          .build();
        }

        // Verificar permissões
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User actor = actorOpt.get();
        if (!isAllowedToAdministrate(tenantId, actor, user)) {
            if (actor.role == Role.OWNER) {
                return Response.status(Response.Status.FORBIDDEN)
                          .entity(new JsonObject().put("code", "OWNER_PROTECTED")
                                                  .put("message", "Cannot delete owner"))
                          .build();
            } else {
                return Response.status(Response.Status.FORBIDDEN)
                          .entity(new JsonObject().put("code", "FORBIDDEN_ROLE")
                                                  .put("message", "Forbidden role"))
                          .build();
            }
        }

        // Verificar se o usuário é o último owner
        if (user.role == Role.OWNER && store.countOwners(tenantId) == 1) {
            return Response.status(Response.Status.CONFLICT)
                      .entity(new JsonObject().put("code", "LAST_OWNER")
                                              .put("message", "Cannot delete last owner"))
                      .build();
        }

        // Realizar a exclusão (soft delete)
        user.status = UserStatus.DELETED;
        user.deletedAt = Instant.now();
        user.purgeAt = Instant.now().plus(30, java.time.temporal.TemporalUnit.NANOS);

        // Registrar auditoria
        AuditEntry audit = new AuditEntry();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_SOFT_DELETED";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "User deleted by " + actorId;
        store.auditLog.add(audit);

        return Response.noContent().build();
    }

    private boolean isAllowedToAdministrate(String tenantId, User actor, User target) {
        // Verificar se o ator é do mesmo tenant
        if (!actor.tenantId.equals(tenantId)) {
            return false;
        }

        // Verificar se o ator tem permissão para administrar
        if (actor.role == Role.MEMBER) {
            return false;
        }

        // Verificar se o ator não está tentando excluir um owner
        if (target.role == Role.OWNER && actor.role == Role.ADMIN) {
            return false;
        }

        return true;
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
.UserResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[67,35] cannot find symbol
  symbol:   class JsonObject
  location: class com.bench.api.UserResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[75,78] cannot find symbol
  symbol:   variable NANOS
  location: interface java.time.temporal.TemporalUnit
[INFO] 6 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.464 s
[INFO] Finished at: 2026-07-19T15:28:25Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[37,51] cannot find symbol
[ERROR]   symbol:   variable UNPROCESSABLE_ENTITY
[ERROR]   location: class jakarta.ws.rs.core.Response.Status
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[38,39] cannot find symbol
[ERROR]   symbol:   class JsonObject
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[53,39] cannot find symbol
[ERROR]   symbol:   class JsonObject
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[58,39] cannot find symbol
[ERROR]   symbol:   class JsonObject
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[67,35] cannot find symbol
[ERROR]   symbol:   class JsonObject
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[75,78] cannot find symbol
[ERROR]   symbol:   variable NANOS
[ERROR]   location: interface java.time.temporal.TemporalUnit
[ERROR] -> [Help 1]
[ERROR] 
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR] 
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoFailureException

```

Corrija e reenvie TODOS os blocos FILE, com o conteúdo completo de cada arquivo.

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
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(@PathParam("tenantId") String tenantId, 
                              @PathParam("userId") String userId, 
                              @HeaderParam("X-Actor-Id") String actorId) {
        // Verificar se o usuário existe
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User user = userOpt.get();
        
        // Verificar se o ator é do mesmo tenant
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Verificar se o ator está tentando excluir a si mesmo
        if (actorId.equals(userId)) {
            return Response.status(Response.Status.UNPROCESSABLE_ENTITY)
                          .entity(new JsonObject().put("code", "CANNOT_DELETE_SELF")
                                                  .put("message", "Cannot delete yourself"))
                          .build();
        }

        // Verificar permissões
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User actor = actorOpt.get();
        if (!isAllowedToAdministrate(tenantId, actor, user)) {
            if (actor.role == Role.OWNER) {
                return Response.status(Response.Status.FORBIDDEN)
                          .entity(new JsonObject().put("code", "OWNER_PROTECTED")
                                                  .put("message", "Cannot delete owner"))
                          .build();
            } else {
                return Response.status(Response.Status.FORBIDDEN)
                          .entity(new JsonObject().put("code", "FORBIDDEN_ROLE")
                                                  .put("message", "Forbidden role"))
                          .build();
            }
        }

        // Verificar se o usuário é o último owner
        if (user.role == Role.OWNER && store.countOwners(tenantId) == 1) {
            return Response.status(Response.Status.CONFLICT)
                      .entity(new JsonObject().put("code", "LAST_OWNER")
                                              .put("message", "Cannot delete last owner"))
                      .build();
        }

        // Realizar a exclusão (soft delete)
        user.status = UserStatus.DELETED;
        user.deletedAt = Instant.now();
        user.purgeAt = Instant.now().plus(30, java.time.temporal.TemporalUnit.NANOS);

        // Registrar auditoria
        AuditEntry audit = new AuditEntry();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_SOFT_DELETED";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "User deleted by " + actorId;
        store.auditLog.add(audit);

        return Response.noContent().build();
    }

    private boolean isAllowedToAdministrate(String tenantId, User actor, User target) {
        // Verificar se o ator é do mesmo tenant
        if (!actor.tenantId.equals(tenantId)) {
            return false;
        }

        // Verificar se o ator tem permissão para administrar
        if (actor.role == Role.MEMBER) {
            return false;
        }

        // Verificar se o ator não está tentando excluir um owner
        if (target.role == Role.OWNER && actor.role == Role.ADMIN) {
            return false;
        }

        return true;
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
.UserResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[67,35] cannot find symbol
  symbol:   class JsonObject
  location: class com.bench.api.UserResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[75,78] cannot find symbol
  symbol:   variable NANOS
  location: interface java.time.temporal.TemporalUnit
[INFO] 6 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.420 s
[INFO] Finished at: 2026-07-19T15:29:22Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[37,51] cannot find symbol
[ERROR]   symbol:   variable UNPROCESSABLE_ENTITY
[ERROR]   location: class jakarta.ws.rs.core.Response.Status
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[38,39] cannot find symbol
[ERROR]   symbol:   class JsonObject
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[53,39] cannot find symbol
[ERROR]   symbol:   class JsonObject
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[58,39] cannot find symbol
[ERROR]   symbol:   class JsonObject
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[67,35] cannot find symbol
[ERROR]   symbol:   class JsonObject
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UserResource.java:[75,78] cannot find symbol
[ERROR]   symbol:   variable NANOS
[ERROR]   location: interface java.time.temporal.TemporalUnit
[ERROR] -> [Help 1]
[ERROR] 
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR] 
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoFailureException

```

Corrija e reenvie TODOS os blocos FILE, com o conteúdo completo de cada arquivo.

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
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(@PathParam("tenantId") String tenantId, 
                              @PathParam("userId") String userId, 
                              @HeaderParam("X-Actor-Id") String actorId) {
        // Verificar se o usuário existe
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User user = userOpt.get();
        
        // Verificar se o ator é do mesmo tenant
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Verificar se o ator está tentando excluir a si mesmo
        if (actorId.equals(userId)) {
            return Response.status(Response.Status.UNPROCESSABLE_ENTITY)
                          .entity("{\"code\": \"CANNOT_DELETE_SELF\", \"message\": \"Cannot delete yourself\"}")
                          .build();
        }

        // Verificar permissões
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User actor = actorOpt.get();
        if (!isAllowedToAdministrate(tenantId, actor, user)) {
            if (actor.role == Role.OWNER) {
                return Response.status(Response.Status.FORBIDDEN)
                          .entity("{\"code\": \"OWNER_PROTECTED\", \"message\": \"Cannot delete owner\"}")
                          .build();
            } else {
                return Response.status(Response.Status.FORBIDDEN)
                          .entity("{\"code\": \"FORBIDDEN_ROLE\", \"message\": \"Forbidden role\"}")
                          .build();
            }
        }

        // Verificar se o usuário é o último owner
        if (user.role == Role.OWNER && store.countOwners(tenantId) == 1) {
            return Response.status(Response.Status.CONFLICT)
                      .entity("{\"code\": \"LAST_OWNER\", \"message\": \"Cannot delete last owner\"}")
                      .build();
        }

        // Realizar a exclusão (soft delete)
        user.status = UserStatus.DELETED;
        user.deletedAt = Instant.now();
        user.purgeAt = Instant.now().plus(30, java.time.temporal.ChronoUnit.DAYS);

        // Registrar auditoria
        AuditEntry audit = new AuditEntry();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_SOFT_DELETED";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "User deleted by " + actorId;
        store.auditLog.add(audit);

        return Response.noContent().build();
    }

    private boolean isAllowedToAdministrate(String tenantId, User actor, User target) {
        // Verificar se o ator é do mesmo tenant
        if (!actor.tenantId.equals(tenantId)) {
            return false;
        }

        // Verificar se o ator tem permissão para administrar
        if (actor.role == Role.MEMBER) {
            return false;
        }

        // Verificar se o ator não está tentando excluir um owner
        if (target.role == Role.OWNER && actor.role == Role.ADMIN) {
            return false;
        }

        return true;
    }
}
```