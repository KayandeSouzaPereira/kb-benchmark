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
FILE: caminho/relativo/do/Arquivo.java
```java
<conteúdo completo do arquivo>
```

ACTION: grep -r "user.*delete\|delete.*user" .
ACTION: read regras/negocio.md
ACTION: read convencoes/erros.md
ACTION: read convencoes/auditoria.md
ACTION: read regras/permissoes.md
ACTION: read regras/validacoes.md
ACTION: read api/users.md
ACTION: read modelo/dados.md

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

(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

ACTION: grep -r "DELETE.*user\|user.*DELETE" 202604010900-mapa-api-e-convencoes.md
ACTION: read 202603150930-quem-pode-deletar.md
ACTION: read 202603150900-soft-delete-30-dias.md
ACTION: read 202602101415-protecao-do-owner.md
ACTION: read 202602101430-ultimo-owner.md
ACTION: read 202602041100-expiracao-de-convites-72h.md
ACTION: read 202605021430-convites-pendentes-contam.md
ACTION: read 202601201330-codigos-de-erro-da-api.md

---

## user

RESULT (6 ações restantes):
nenhum resultado para: -r "DELETE.*user\|user.*DELETE" 202604010900-mapa-api-e-convencoes.md

---

## assistant

ACTION: grep -r "DELETE" 202604010900-mapa-api-e-convencoes.md
ACTION: read 202601201300-auditoria-de-mutacoes.md
ACTION: read 202605190800-ideias-de-precos.md
ACTION: read 202601051030-papeis-do-tenant.md
ACTION: read 202601121000-limites-por-plano.md
ACTION: read 202601080800-lockout-e-senhas.md
ACTION: read 202602041130-reenvio-de-convites.md

---

## user

RESULT (5 ações restantes):
nenhum resultado para: -r "DELETE" 202604010900-mapa-api-e-convencoes.md

---

## assistant

ACTION: ls com/bench/api/
ACTION: read com/bench/api/UsuariosResource.java
ACTION: read com/bench/api/BaseResource.java
ACTION: read com/bench/api/HealthResource.java
ACTION: read com/bench/api/TenantsResource.java
ACTION: read com/bench/api/UsersResource.java
ACTION: read com/bench/api/InvitationsResource.java

---

## user

RESULT (4 ações restantes):
não existe: com/bench/api/

---

## assistant

ACTION: ls src/main/java/com/bench/api/
FILE: src/main/java/com/bench/api/BaseResource.java
```java
package com.bench.api;

import jakarta.ws.rs.core.Context;
import jakarta.ws.rs.core.HttpHeaders;
import jakarta.ws.rs.core.Response;

public class BaseResource {
    @Context
    protected HttpHeaders headers;

    protected String getActorId() {
        return headers.getHeaderString("X-Actor-Id");
    }

    protected Response notFound() {
        return Response.status(404).build();
    }

    protected Response forbidden() {
        return Response.status(403).build();
    }

    protected Response unprocessableEntity(String message) {
        return Response.status(422).entity(message).build();
    }
}
```

FILE: src/main/java/com/bench/api/UsersResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Path("/tenants/{tenantId}/users")
public class UsersResource extends BaseResource {

    @Inject
    InMemoryStore store;

    @DELETE
    @Path("/{userId}")
    public Response deleteUser(@PathParam("tenantId") String tenantId, @PathParam("userId") String userId) {
        String actorId = getActorId();

        // 1. Validação do tenant e usuário
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return notFound();
        }
        User targetUser = targetUserOpt.get();

        if (!targetUser.tenantId.equals(tenantId)) {
            return notFound();
        }

        // 2. Validação do ator
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return forbidden();
        }
        User actor = actorOpt.get();

        if (!actor.tenantId.equals(tenantId)) {
            return forbidden();
        }

        // 3. Permissões: somente OWNER ou ADMIN podem deletar
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return forbidden();
        }

        // 4. Não pode deletar o próprio usuário se for OWNER e for o único OWNER
        if (targetUser.id.equals(actorId) && targetUser.role == Role.OWNER) {
            long ownersCount = store.countOwners(tenantId);
            if (ownersCount <= 1) {
                return unprocessableEntity("Não é possível excluir o último OWNER do tenant.");
            }
        }

        // 5. Soft delete: atualiza status e define deletedAt
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = Instant.now();

        // 6. Auditoria
        AuditEntry audit = new AuditEntry();
        audit.id = "audit-" + Instant.now().toEpochMilli();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "DELETE_USER";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "User deleted by actor " + actorId;

        store.auditLog.add(audit);

        return Response.noContent().build();
    }
}
```

---

## user

RESULT (3 ações restantes):
não existe: src/main/java/com/bench/api/

(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

ACTION: ls src/main/java/com/bench/
ACTION: read src/main/java/com/bench/api/UsersResource.java
FILE: src/main/java/com/bench/api/UsersResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Path("/tenants/{tenantId}/users")
public class UsersResource extends BaseResource {

    @Inject
    InMemoryStore store;

    @DELETE
    @Path("/{userId}")
    public Response deleteUser(@PathParam("tenantId") String tenantId, @PathParam("userId") String userId) {
        String actorId = getActorId();

        // 1. Validação do tenant e usuário
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return notFound();
        }
        User targetUser = targetUserOpt.get();

        if (!targetUser.tenantId.equals(tenantId)) {
            return notFound();
        }

        // 2. Validação do ator
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return forbidden();
        }
        User actor = actorOpt.get();

        if (!actor.tenantId.equals(tenantId)) {
            return forbidden();
        }

        // 3. Permissões: somente OWNER ou ADMIN podem deletar
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return forbidden();
        }

        // 4. Não pode deletar o próprio usuário se for OWNER e for o único OWNER
        if (targetUser.id.equals(actorId) && targetUser.role == Role.OWNER) {
            long ownersCount = store.countOwners(tenantId);
            if (ownersCount <= 1) {
                return unprocessableEntity("Não é possível excluir o último OWNER do tenant.");
            }
        }

        // 5. Soft delete: atualiza status e define deletedAt
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = Instant.now();

        // 6. Auditoria
        AuditEntry audit = new AuditEntry();
        audit.id = "audit-" + Instant.now().toEpochMilli();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "DELETE_USER";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "User deleted by actor " + actorId;

        store.auditLog.add(audit);

        return Response.noContent().build();
    }
}
```

---

## user

RESULT (2 ações restantes):
não existe: src/main/java/com/bench/

(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

ACTION: ls src/main/java/
FILE: src/main/java/com/bench/api/UsersResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Path("/tenants/{tenantId}/users")
public class UsersResource extends BaseResource {

    @Inject
    InMemoryStore store;

    @DELETE
    @Path("/{userId}")
    public Response deleteUser(@PathParam("tenantId") String tenantId, @PathParam("userId") String userId) {
        String actorId = getActorId();

        // 1. Validação do tenant e usuário
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return notFound();
        }
        User targetUser = targetUserOpt.get();

        if (!targetUser.tenantId.equals(tenantId)) {
            return notFound();
        }

        // 2. Validação do ator
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return forbidden();
        }
        User actor = actorOpt.get();

        if (!actor.tenantId.equals(tenantId)) {
            return forbidden();
        }

        // 3. Permissões: somente OWNER ou ADMIN podem deletar
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return forbidden();
        }

        // 4. Não pode deletar o próprio usuário se for OWNER e for o único OWNER
        if (targetUser.id.equals(actorId) && targetUser.role == Role.OWNER) {
            long ownersCount = store.countOwners(tenantId);
            if (ownersCount <= 1) {
                return unprocessableEntity("Não é possível excluir o último OWNER do tenant.");
            }
        }

        // 5. Soft delete: atualiza status e define deletedAt
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = Instant.now();

        // 6. Auditoria
        AuditEntry audit = new AuditEntry();
        audit.id = "audit-" + Instant.now().toEpochMilli();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "DELETE_USER";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "User deleted by actor " + actorId;

        store.auditLog.add(audit);

        return Response.noContent().build();
    }
}
```

---

## user

RESULT (1 ações restantes):
não existe: src/main/java/

(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

FILE: src/main/java/com/bench/api/UsersResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Path("/tenants/{tenantId}/users")
public class UsersResource extends BaseResource {

    @Inject
    InMemoryStore store;

    @DELETE
    @Path("/{userId}")
    public Response deleteUser(@PathParam("tenantId") String tenantId, @PathParam("userId") String userId) {
        String actorId = getActorId();

        // 1. Validação do tenant e usuário
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return notFound();
        }
        User targetUser = targetUserOpt.get();

        if (!targetUser.tenantId.equals(tenantId)) {
            return notFound();
        }

        // 2. Validação do ator
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return forbidden();
        }
        User actor = actorOpt.get();

        if (!actor.tenantId.equals(tenantId)) {
            return forbidden();
        }

        // 3. Permissões: somente OWNER ou ADMIN podem deletar
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return forbidden();
        }

        // 4. Não pode deletar o próprio usuário se for OWNER e for o único OWNER
        if (targetUser.id.equals(actorId) && targetUser.role == Role.OWNER) {
            long ownersCount = store.countOwners(tenantId);
            if (ownersCount <= 1) {
                return unprocessableEntity("Não é possível excluir o último OWNER do tenant.");
            }
        }

        // 5. Soft delete: atualiza status e define deletedAt
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = Instant.now();

        // 6. Auditoria
        AuditEntry audit = new AuditEntry();
        audit.id = "audit-" + Instant.now().toEpochMilli();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "DELETE_USER";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "User deleted by actor " + actorId;

        store.auditLog.add(audit);

        return Response.noContent().build();
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
i.UsersResource
[INFO] 8 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.204 s
[INFO] Finished at: 2026-07-19T17:54:47Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UsersResource.java:[14,36] cannot find symbol
[ERROR]   symbol: class BaseResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UsersResource.java:[22,26] cannot find symbol
[ERROR]   symbol:   method getActorId()
[ERROR]   location: class com.bench.api.UsersResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UsersResource.java:[27,20] cannot find symbol
[ERROR]   symbol:   method notFound()
[ERROR]   location: class com.bench.api.UsersResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UsersResource.java:[32,20] cannot find symbol
[ERROR]   symbol:   method notFound()
[ERROR]   location: class com.bench.api.UsersResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UsersResource.java:[38,20] cannot find symbol
[ERROR]   symbol:   method forbidden()
[ERROR]   location: class com.bench.api.UsersResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UsersResource.java:[43,20] cannot find symbol
[ERROR]   symbol:   method forbidden()
[ERROR]   location: class com.bench.api.UsersResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UsersResource.java:[48,20] cannot find symbol
[ERROR]   symbol:   method forbidden()
[ERROR]   location: class com.bench.api.UsersResource
[ERROR] /work/vault-b/t2/src/main/java/com/bench/api/UsersResource.java:[55,24] cannot find symbol
[ERROR]   symbol:   method unprocessableEntity(java.lang.String)
[ERROR]   location: class com.bench.api.UsersResource
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

ACTION: ls src/main/java/com/bench/api/
ACTION: read src/main/java/com/bench/api/BaseResource.java
FILE: src/main/java/com/bench/api/BaseResource.java
```java
package com.bench.api;

import jakarta.ws.rs.core.Context;
import jakarta.ws.rs.core.HttpHeaders;
import jakarta.ws.rs.core.Response;

public class BaseResource {
    @Context
    protected HttpHeaders headers;

    protected String getActorId() {
        return headers.getHeaderString("X-Actor-Id");
    }

    protected Response notFound() {
        return Response.status(404).build();
    }

    protected Response forbidden() {
        return Response.status(403).build();
    }

    protected Response unprocessableEntity(String message) {
        return Response.status(422).entity(message).build();
    }
}
```

FILE: src/main/java/com/bench/api/UsersResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Path("/tenants/{tenantId}/users")
public class UsersResource extends BaseResource {

    @Inject
    InMemoryStore store;

    @DELETE
    @Path("/{userId}")
    public Response deleteUser(@PathParam("tenantId") String tenantId, @PathParam("userId") String userId) {
        String actorId = getActorId();

        // 1. Validação do tenant e usuário
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return notFound();
        }
        User targetUser = targetUserOpt.get();

        if (!targetUser.tenantId.equals(tenantId)) {
            return notFound();
        }

        // 2. Validação do ator
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return forbidden();
        }
        User actor = actorOpt.get();

        if (!actor.tenantId.equals(tenantId)) {
            return forbidden();
        }

        // 3. Permissões: somente OWNER ou ADMIN podem deletar
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return forbidden();
        }

        // 4. Não pode deletar o próprio usuário se for OWNER e for o único OWNER
        if (targetUser.id.equals(actorId) && targetUser.role == Role.OWNER) {
            long ownersCount = store.countOwners(tenantId);
            if (ownersCount <= 1) {
                return unprocessableEntity("Não é possível excluir o último OWNER do tenant.");
            }
        }

        // 5. Soft delete: atualiza status e define deletedAt
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = Instant.now();

        // 6. Auditoria
        AuditEntry audit = new AuditEntry();
        audit.id = "audit-" + Instant.now().toEpochMilli();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "DELETE_USER";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "User deleted by actor " + actorId;

        store.auditLog.add(audit);

        return Response.noContent().build();
    }
}
```