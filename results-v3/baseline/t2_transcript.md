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

FILE: src/main/java/com/bench/api/UserResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.time.Duration;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // 1. Validação de parâmetros
        if (tenantId == null || tenantId.isEmpty() || userId == null || userId.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST).build();
        }

        // 2. Verifica se o usuário autenticado existe
        Optional<User> actorUserOpt = store.findUser(actorId);
        if (actorUserOpt.isEmpty()) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        User actorUser = actorUserOpt.get();

        // 3. Verifica se o usuário alvo existe
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User targetUser = targetUserOpt.get();

        // 4. Verifica se o usuário alvo pertence ao tenant
        if (!targetUser.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // 5. Verifica se o usuário alvo está ativo
        if (targetUser.status == UserStatus.DELETED) {
            return Response.status(Response.Status.GONE).build();
        }

        // 6. Verifica se o usuário alvo é o único dono do tenant
        if (targetUser.role == Role.OWNER) {
            long ownerCount = store.countOwners(tenantId);
            if (ownerCount == 1) {
                return Response.status(Response.Status.FORBIDDEN).build();
            }
        }

        // 7. Verifica se o usuário autenticado tem permissão para excluir
        if (actorUser.role == Role.MEMBER) {
            // Verifica se o usuário autenticado é o dono do tenant
            if (!actorUser.role.equals(Role.OWNER)) {
                return Response.status(Response.INSUFFICIENT_STORAGE).build();
            }
        }

        // 8. Verifica se o usuário autenticado é o dono do tenant
        if (actorUser.role != Role.OWNER && actorUser.role != Role.ADMIN) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // 9. Verifica se o usuário alvo não está em um plano com limite de usuários
        Optional<Tenant> tenantOpt = store.findUser(tenantId);
        if (tenantOpt.isPresent()) {
            Tenant tenant = tenantOpt.get();
            if (tenant.plan != Plan.FREE && tenant.plan != Plan.PRO && tenant.plan != Plan.ENTERPRISE) {
                return Response.status(Response.Status.FORBIDDEN).build();
            }

            if (tenant.plan == Plan.FREE || tenant.plan == Plan.PRO) {
                if (tenant.plan == Plan.FREE && tenant.maxUsers != null && tenant.maxUsers <= store.usersOfTenant(tenantId).size()) {
                    return Response.status(Response.Status.FORBIDDEN).build();
                }

                if (tenant.plan == Plan.PRO && tenant.maxUsers != null && tenant.maxUsers <= store.usersOfTenant(tenantId).size()) {
                    return Response.status(Response.Status.FORBIDDEN).build();
                }
            }
        }

        // 10. Marca o usuário como deletado
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = Instant.now();

        // 11. Registra a ação no log de auditoria
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "DELETE_USER";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "User " + userId + " was deleted by " + actorId;

        store.auditLog.add(auditEntry);

        // 12. Retorna resposta 204 No Content
        return Response.noContent().build();
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
annot find symbol
  symbol:   variable maxUsers
  location: variable tenant of type com.bench.model.Tenant
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[91,81] cannot find symbol
  symbol:   variable maxUsers
  location: variable tenant of type com.bench.model.Tenant
[INFO] 6 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.489 s
[INFO] Finished at: 2026-07-19T15:51:45Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[69,48] cannot find symbol
[ERROR]   symbol:   variable INSUFFICIENT_STORAGE
[ERROR]   location: class jakarta.ws.rs.core.Response
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[79,52] incompatible types: java.util.Optional<com.bench.model.User> cannot be converted to java.util.Optional<com.bench.model.Tenant>
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[87,55] cannot find symbol
[ERROR]   symbol:   variable maxUsers
[ERROR]   location: variable tenant of type com.bench.model.Tenant
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[87,82] cannot find symbol
[ERROR]   symbol:   variable maxUsers
[ERROR]   location: variable tenant of type com.bench.model.Tenant
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[91,54] cannot find symbol
[ERROR]   symbol:   variable maxUsers
[ERROR]   location: variable tenant of type com.bench.model.Tenant
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[91,81] cannot find symbol
[ERROR]   symbol:   variable maxUsers
[ERROR]   location: variable tenant of type com.bench.model.Tenant
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
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.time.Duration;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // 1. Validação de parâmetros
        if (tenantId == null || tenantId.isEmpty() || userId == null || userId.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST).build();
        }

        // 2. Verifica se o usuário autenticado existe
        Optional<User> actorUserOpt = store.findUser(actorId);
        if (actorUserOpt.isEmpty()) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        User actorUser = actorUserOpt.get();

        // 3. Verifica se o usuário alvo existe
        Optional<User> targetUserOpt = store.find
```

---

## user

A compilação/verificação do seu código falhou:

```
sem relatorio surefire (compilacao?)
[INFO] Scanning for projects...
[INFO] 
[INFO] ------------------------< com.bench:saas-users >------------------------
[INFO] Building saas-users 1.0.0
[INFO]   from pom.xml
[INFO] --------------------------------[ jar ]---------------------------------
[INFO] 
[INFO] --- resources:3.4.0:resources (default-resources) @ saas-users ---
[INFO] Copying 1 resource from src/main/resources to target/classes
[INFO] 
[INFO] --- compiler:3.15.0:compile (default-compile) @ saas-users ---
[INFO] Recompiling the module because of changed source code.
[INFO] Compiling 10 source files with javac [debug release 21] to target/classes
[INFO] -------------------------------------------------------------
[ERROR] COMPILATION ERROR : 
[INFO] -------------------------------------------------------------
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[40,50] reached end of file while parsing
[INFO] 1 error
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.185 s
[INFO] Finished at: 2026-07-19T15:52:06Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[40,50] reached end of file while parsing
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
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.time.Duration;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // 1. Validação de parâmetros
        if (tenantId == null || tenantId.isEmpty() || userId == null || userId.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST).build();
        }

        // 2. Verifica se o usuário autenticado existe
        Optional<User> actorUserOpt = store.findUser(actorId);
        if (actorUserOpt.isEmpty()) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        User actorUser = actorUserOpt.get();

        // 3. Verifica se o usuário alvo existe
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User targetUser = targetUserOpt.get();

        // 4. Verifica se o usuário alvo pertence ao tenant
        if (!targetUser.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // 5. Verifica se o usuário alvo está ativo
        if (targetUser.status == UserStatus.DELETED) {
            return Response.status(Response.Status.GONE).build();
        }

        // 6. Verifica se o usuário alvo é o único dono do tenant
        if (targetUser.role == Role.OWNER) {
            long ownerCount = store.countOwners(tenantId);
            if (ownerCount == 1) {
                return Response.status(Response.Status.FORBIDDEN).build();
            }
        }

        // 7. Verifica se o usuário autenticado tem permissão para excluir
        if (actorUser.role == Role.MEMBER) {
            // Verifica se o usuário autenticado é o dono do tenant
            if (!actorUser.role.equals(Role.OWNER)) {
                return Response.status(Response.Status.FORBIDDEN).build();
            }
        }

        // 8. Verifica se o usuário autenticado é o dono do tenant ou administrador
        if (actorUser.role != Role.OWNER && actorUser.role != Role.ADMIN) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // 9. Verifica se o plano do tenant permite a exclusão do usuário
        Optional<Tenant> tenantOpt = store.findUser(tenantId);
        if (tenantOpt.isPresent()) {
            Tenant tenant = tenantOpt.get();
            if (tenant.plan == Plan.ENTERPRISE) {
                // Plano Enterprise não tem limite de usuários
                return Response.status(Response.Status.OK).build();
            } else if (tenant.plan == Plan.PRO) {
                // Verifica se o limite de usuários foi atingido
                int currentUsers = store.usersOfTenant(tenantId).size();
                if (tenant.maxUsers != null && tenant.maxUsers <= currentUsers) {
                    return Response.status(Response.Status.FORBIDDEN).build();
                }
            } else if (tenant.plan == Plan.FREE) {
                // Plano Free também tem limite de usuários
                int currentUsers = store.usersOfTenant(tenantId).size();
                if (tenant.maxUsers != null && tenant.maxUsers <= currentUsers) {
                    return Response.status(Response.Status.FORBIDDEN).build();
                }
            }
        }

        // 10. Marca o usuário como deletado
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = Instant.now();

        // 11. Registra a ação no log de auditoria
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "DELETE_USER";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "User " + userId + " was deleted by " + actorId;

        store.auditLog.add(auditEntry);

        // 12. Retorna resposta 204 No Content
        return Response.noContent().build();
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
.java:[88,54] cannot find symbol
  symbol:   variable maxUsers
  location: variable tenant of type com.bench.model.Tenant
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[94,27] cannot find symbol
  symbol:   variable maxUsers
  location: variable tenant of type com.bench.model.Tenant
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[94,54] cannot find symbol
  symbol:   variable maxUsers
  location: variable tenant of type com.bench.model.Tenant
[INFO] 5 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.510 s
[INFO] Finished at: 2026-07-19T15:53:09Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[79,52] incompatible types: java.util.Optional<com.bench.model.User> cannot be converted to java.util.Optional<com.bench.model.Tenant>
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[88,27] cannot find symbol
[ERROR]   symbol:   variable maxUsers
[ERROR]   location: variable tenant of type com.bench.model.Tenant
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[88,54] cannot find symbol
[ERROR]   symbol:   variable maxUsers
[ERROR]   location: variable tenant of type com.bench.model.Tenant
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[94,27] cannot find symbol
[ERROR]   symbol:   variable maxUsers
[ERROR]   location: variable tenant of type com.bench.model.Tenant
[ERROR] /work/baseline/t2/src/main/java/com/bench/api/UserResource.java:[94,54] cannot find symbol
[ERROR]   symbol:   variable maxUsers
[ERROR]   location: variable tenant of type com.bench.model.Tenant
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
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.time.Duration;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // 1. Validação de parâmetros
        if (tenantId == null || tenantId.isEmpty() || userId == null || userId.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST).build();
        }

        // 2. Verifica se o usuário autenticado existe
        Optional<User> actorUserOpt = store.findUser(actorId);
        if (actorUserOpt.isEmpty()) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        User actorUser = actorUserOpt.get();

        // 3. Verifica se o usuário alvo existe
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User targetUser = targetUserOpt.get();

        // 4. Verifica se o usuário alvo pertence ao tenant
        if (!targetUser.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // 5. Verifica se o usuário alvo está ativo
        if (targetUser.status == UserStatus.DELETED) {
            return Response.status(Response.Status.GONE).build();
        }

        // 6. Verifica se o usuário alvo é o único dono do tenant
        if (targetUser.role == Role.OWNER) {
            long ownerCount = store.countOwners(tenantId);
            if (ownerCount == 1) {
                return Response.status(Response.Status.FORBIDDEN).build();
            }
        }

        // 7. Verifica se o usuário autenticado tem permissão para excluir
        if (actorUser.role == Role.MEMBER) {
            // Verifica se o usuário autenticado é o dono do tenant
            if (!actorUser.role.equals(Role.OWNER)) {
                return Response.status(Response.Status.FORBIDDEN).build();
            }
        }

        // 8. Verifica se o usuário autenticado é o dono do tenant ou administrador
        if (actorUser.role != Role.OWNER && actorUser.role != Role.ADMIN) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // 9. Verifica se o plano do tenant permite a exclusão do usuário
        Optional<Tenant> tenantOpt = store.findUser(tenantId);
        if (tenantOpt.isPresent()) {
            Tenant tenant = tenantOpt.get();
            if (tenant.plan == Plan.ENTERPRISE) {
                // Plano Enterprise não tem limite de usuários
                return Response.status(Response.Status.OK).build();
            } else if (tenant.plan == Plan.PRO || tenant.plan == Plan.FREE) {
                // Verifica se o limite de usuários foi atingido
                int currentUsers = store.usersOfTenant(tenantId).size();
                if (tenant.maxUsers != null && tenant.maxUsers <= currentUsers) {
                    return Response.status(Response.Status.FORBIDDEN).build();
                }
            }
        }

        // 10. Marca o usuário como deletado
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = Instant.now();

        // 11. Registra a ação no log de auditoria
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "DELETE_USER";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "User " + userId + " was deleted by " + actorId;

        store.auditLog.add(auditEntry);

        // 12. Retorna resposta 204 No Content
        return Response.noContent().build();
    }
}
```