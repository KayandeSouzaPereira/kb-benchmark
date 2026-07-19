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

FILE: src/main/java/com/bench/api/RoleResource.java
```java
package com.bench.api;

import com.bench.model.Role;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.model.Invitation;
import com.bench.model.AuditEntry;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}/role")
public class RoleResource {

    @Inject
    InMemoryStore store;

    @PATCH
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response changeRole(@PathParam("tenantId") String tenantId,
                              @PathParam("userId") String userId,
                              @HeaderParam("X-Actor-Id") String actorId,
                              Role newRole) {
        // Validação do novo papel
        if (newRole == null || !newRole.equals(Role.OWNER) && !newRole.equals(Role.ADMIN) && !newRole.equals(Role.MEMBER)) {
            return Response.status(Response.Status.BAD_REQUEST).entity("Invalid role").build();
        }

        // Busca o usuário
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).entity("User not found").build();
        }

        User user = userOpt.get();
        String userTenantId = user.tenantId;

        // Verifica se o usuário pertence ao tenant
        if (!userTenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).entity("User not part of this tenant").build();
        }

        // Verifica se o usuário está ativo
        if (user.status == UserStatus.DELETED || user.status == UserStatus.SUSPENDED) {
            return Response.status(Response, Status.FORBIDDEN).entity("User is not active").build();
        }

        // Verifica se o usuário já é o novo papel
        if (user.role == newRole) {
            return Response.status(Response.Status.OK).entity(user).build();
        }

        // Verifica se o novo papel é permitido com base no plano do tenant
        Optional<Tenant> tenantOpt = store.findUser(tenantId); // Busca o tenant (aqui, o tenantId é o id do tenant)
        if (tenantOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).entity("Tenant not found").build();
        }

        Tenant tenant = tenantOpt.get();
        Plan plan = tenant.plan;

        // Verifica se o novo papel é permitido com base no plano do tenant
        if (plan == Plan.FREE && newRole == Role.OWNER) {
            return Response.status(Response.Status.FORBIDDEN).entity("OWNER role is not allowed in FREE plan").build();
        }

        // Verifica se o novo papel é permitido com base no plano do tenant
        if (plan == Plan.FREE && newRole == Role.ADMIN && store.countOwners(tenantId) >= 1) {
            return Response.status(Response.Status.FORBIDDEN).entity("Only one OWNER is allowed in FREE plan").build();
        }

        // Verifica se o novo papel é permitido com base no plano do tenant
        if (plan == Plan.FREE && newRole == Role.ADMIN && store.countOwners(tenantId) >= 1) {
            return Response.status(Response.Status.FORBIDDEN).entity("Only one OWNER is allowed in FREE plan").build();
        }

        // Verifica se o novo papel é permitido com base no plano do tenant
        if (plan == Plan.FREE && newRole == Role.ADMIN && store.countOwners(tenantId) >= 1) {
            return Response.status(Response.Status.FORBIDDEN).entity("Only one OWNER is allowed in FREE plan").build();
        }

        // Atualiza o papel do usuário
        user.role = newRole;

        // Registra a ação no audit log
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "CHANGE_ROLE";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "User role changed from " + user.role + " to " + newRole;

        store.auditLog.add(auditEntry);

        return Response.status(Response.Status.OK).entity(user).build();
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
-------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.621 s
[INFO] Finished at: 2026-07-19T16:32:43Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[50,36] cannot find symbol
[ERROR]   symbol:   variable Response
[ERROR]   location: class com.bench.api.RoleResource
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[50,46] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.RoleResource
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[59,18] cannot find symbol
[ERROR]   symbol:   class Tenant
[ERROR]   location: class com.bench.api.RoleResource
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[64,9] cannot find symbol
[ERROR]   symbol:   class Tenant
[ERROR]   location: class com.bench.api.RoleResource
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[65,9] cannot find symbol
[ERROR]   symbol:   class Plan
[ERROR]   location: class com.bench.api.RoleResource
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[68,21] cannot find symbol
[ERROR]   symbol:   variable Plan
[ERROR]   location: class com.bench.api.RoleResource
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[73,21] cannot find symbol
[ERROR]   symbol:   variable Plan
[ERROR]   location: class com.bench.api.RoleResource
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[78,21] cannot find symbol
[ERROR]   symbol:   variable Plan
[ERROR]   location: class com.bench.api.RoleResource
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[83,21] cannot find symbol
[ERROR]   symbol:   variable Plan
[ERROR]   location: class com.bench.api.RoleResource
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

FILE: src/main/java/com/bench/api/RoleResource.java
```java
package com.bench.api;

import com.bench.model.Role;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.model.Invitation;
import com.bench.model.AuditEntry;
import com.bench.model.Tenant;
import com.bench.model.Plan;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}/role")
public class RoleResource {

    @Inject
    InMemoryStore store;

    @PATCH
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response changeRole(@PathParam("tenantId") String tenantId,
                              @PathParam("userId") String userId,
                              @HeaderParam("X-Actor-Id") String actorId,
                              Role newRole) {
        // Validação do novo papel
        if (newRole == null || !newRole.equals(Role.OWNER) && !newRole.equals(Role.ADMIN) && !newRole.equals(Role.MEMBER)) {
            return Response.status(Response.Status.BAD_REQUEST).entity("Invalid role").build();
        }

        // Busca o usuário
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).entity("User not found").build();
        }

        User user = userOpt.get();
        String userTenantId = user.tenantId;

        // Verifica se o usuário pertence ao tenant
        if (!userTenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).entity("User not part of this tenant").build();
        }

        // Verifica se o usuário está ativo
        if (user.status == UserStatus.DELETED || user.status == UserStatus.SUSPENDED) {
            return Response.status(Response.Status.FORBIDDEN).entity("User is not active").build();
        }

        // Verifica se o usuário já é o novo papel
        if (user.role == newRole) {
            return Response.status(Response.Status.OK).entity(user).build();
        }

        // Busca o tenant
        Optional<Tenant> tenantOpt = store.findUser(tenantId); // Busca o tenant (aqui, o tenantId é o id do tenant)
        if (tenantOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).entity("Tenant not found").build();
        }

        Tenant tenant = tenantOpt.get();
        Plan plan = tenant.plan;

        // Verifica se o novo papel é permitido com base no plano do tenant
        if (plan == Plan.FREE && newRole == Role.OWNER) {
            return Response.status(Response.Status.FORBIDDEN).entity("OWNER role is not allowed in FREE plan").build();
        }

        // Verifica se o novo papel é permitido com base no plano do tenant
        if (plan == Plan.FREE && newRole == Role.ADMIN && store.countOwners(tenantId) >= 1) {
            return Response.status(Response.Status.FORBIDDEN).entity("Only one OWNER is allowed in FREE plan").build();
        }

        // Atualiza o papel do usuário
        user.role = newRole;

        // Registra a ação no audit log
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "CHANGE_ROLE";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "User role changed from " + user.role + " to " + newRole;

        store.auditLog.add(auditEntry);

        return Response.status(Response.Status.OK).entity(user).build();
    }
}
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
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[61,52] incompatible types: java.util.Optional<com.bench.model.User> cannot be converted to java.util.Optional<com.bench.model.Tenant>
[INFO] 1 error
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.585 s
[INFO] Finished at: 2026-07-19T16:33:37Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[61,52] incompatible types: java.util.Optional<com.bench.model.User> cannot be converted to java.util.Optional<com.bench.model.Tenant>
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

FILE: src/main/java/com/bench/api/RoleResource.java
```java
package com.bench.api;

import com.bench.model.Role;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.model.Tenant;
import com.bench.model.Plan;
import com.bench.model.Invitation;
import com.bench.model.AuditEntry;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}/role")
public class RoleResource {

    @Inject
    InMemoryStore store;

    @PATCH
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response changeRole(@PathParam("tenantId") String tenantId,
                              @PathParam("userId") String userId,
                              @HeaderParam("X-Actor-Id") String actorId,
                              Role newRole) {
        // Validação do novo papel
        if (newRole == null || !newRole.equals(Role.OWNER) && !newRole.equals(Role.ADMIN) && !newRole.equals(Role.MEMBER)) {
            return Response.status(Response.Status.BAD_REQUEST).entity("Invalid role").build();
        }

        // Busca o usuário
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).entity("User not found").build();
        }

        User user = userOpt.get();
        String userTenantId = user.tenantId;

        // Verifica se o usuário pertence ao tenant
        if (!userTenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).entity("User not part of this tenant").build();
        }

        // Verifica se o usuário está ativo
        if (user.status == UserStatus.DELETED || user.status == UserStatus.SUSPENDED) {
            return Response.status(Response.Status.FORBIDDEN).entity("User is not active").build();
        }

        // Verifica se o usuário já é o novo papel
        if (user.role == newRole) {
            return Response.status(Response.Status.OK).entity(user).build();
        }

        // Busca o tenant
        Optional<Tenant> tenantOpt = store.findUser(tenantId); // Busca o tenant (aqui, o tenantId é o id do tenant)
        if (tenantOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).entity("Tenant not found").build();
        }

        Tenant tenant = tenantOpt.get();
        Plan plan = tenant.plan;

        // Verifica se o novo papel é permitido com base no plano do tenant
        if (plan == Plan.FREE && newRole == Role.OWNER) {
            return Response.status(Response.Status.FORBIDDEN).entity("OWNER role is not allowed in FREE plan").build();
        }

        // Verifica se o novo papel é permitido com base no plano do tenant
        if (plan == Plan.FREE && newRole == Role.ADMIN && store.countOwners(tenantId) >= 1) {
            return Response.status(Response.Status.FORBIDDEN).entity("Only one OWNER is allowed in FREE plan").build();
        }

        // Atualiza o papel do usuário
        user.role = newRole;

        // Registra a ação no audit log
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "CHANGE_ROLE";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "User role changed from " + user.role + " to " + newRole;

        store.auditLog.add(auditEntry);

        return Response.status(Response.Status.OK).entity(user).build();
    }
}
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
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[61,52] incompatible types: java.util.Optional<com.bench.model.User> cannot be converted to java.util.Optional<com.bench.model.Tenant>
[INFO] 1 error
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.249 s
[INFO] Finished at: 2026-07-19T16:34:34Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure
[ERROR] /work/baseline/t4/src/main/java/com/bench/api/RoleResource.java:[61,52] incompatible types: java.util.Optional<com.bench.model.User> cannot be converted to java.util.Optional<com.bench.model.Tenant>
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

FILE: src/main/java/com/bench/api/RoleResource.java
```java
package com.bench.api;

import com.bench.model.Role;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.model.Tenant;
import com.bench.model.Plan;
import com.bench.model.Invitation;
import com.bench.model.AuditEntry;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}/role")
public class RoleResource {

    @Inject
    InMemoryStore store;

    @PATCH
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response changeRole(@PathParam("tenantId") String tenantId,
                              @PathParam("userId") String userId,
                              @HeaderParam("X-Actor-Id") String actorId,
                              Role newRole) {
        // Validação do novo papel
        if (newRole == null || !newRole.equals(Role.OWNER) && !newRole.equals(Role.ADMIN) && !newRole.equals(Role.MEMBER)) {
            return Response.status(Response.Status.BAD_REQUEST).entity("Invalid role").build();
        }

        // Busca o usuário
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).entity("User not found").build();
        }

        User user = userOpt.get();
        String userTenantId = user.tenantId;

        // Verifica se o usuário pertence ao tenant
        if (!userTenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).entity("User not part of this tenant").build();
        }

        // Verifica se o usuário está ativo
        if (user.status == UserStatus.DELETED || user.status == UserStatus.SUSPENDED) {
            return Response.status(Response.Status.FORBIDDEN).entity("User is not active").build();
        }

        // Verifica se o usuário já é o novo papel
        if (user.role == newRole) {
            return Response.status(Response.Status.OK).entity(user).build();
        }

        // Busca o tenant
        Optional<Tenant> tenantOpt = store.findUser(tenantId); // Busca o tenant (aqui, o tenantId é o id do tenant)
        if (tenantOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).entity("Tenant not found").build();
        }

        Tenant tenant = tenantOpt.get();
        Plan plan = tenant.plan;

        // Verifica se o novo papel é permitido com base no plano do tenant
        if (plan == Plan.FREE && newRole == Role.OWNER) {
            return Response.status(Response.Status.FORBIDDEN).entity("OWNER role is not allowed in FREE plan").build();
        }

        // Verifica se o novo papel é permitido com base no plano do tenant
        if (plan == Plan.FREE && newRole == Role.ADMIN && store.countOwners(tenantId) >= 1) {
            return Response.status(Response.Status.FORBIDDEN).entity("Only one OWNER is allowed in FREE plan").build();
        }

        // Atualiza o papel do usuário
        user.role = newRole;

        // Registra a ação no audit log
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "CHANGE_ROLE";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "User role changed from " + user.role + " to " + newRole;

        store.auditLog.add(auditEntry);

        return Response.status(Response.Status.OK).entity(user).build();
    }
}
```