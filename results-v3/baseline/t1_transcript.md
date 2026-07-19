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

# Tarefa: criar convite de usuário

Implemente o endpoint de criação de convite:

```
POST /tenants/{tenantId}/invitations
Request JSON:  { "email": "pessoa@ex.com", "role": "ADMIN" | "MEMBER" }
Sucesso: 201 com JSON { "id": "...", "expiresAt": "..." }
```

Persista o convite no `InMemoryStore`. Implemente TODAS as regras de negócio,
permissões, validações e convenções de erro/auditoria que o time definiu para
convites.


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

FILE: src/main/java/com/bench/api/InvitationResource.java
```java
package com.bench.api;

import com.bench.model.Role;
import com.bench.model.Invitation;
import com.bench.model.InvitationStatus;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.model.AuditEntry;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.time.Instant;
import java.time.Duration;
import java.util.*;

@Path("/tenants/{tenantId}/invitations")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class InvitationResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response createInvitation(@PathParam("tenantId") String tenantId, InvitationRequest request) {
        // Validate tenant exists
        if (!store.tenants.containsKey(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).entity("Tenant not found").build();
        }

        // Validate email
        if (request.email == null || request.email.trim().isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST).entity("Email is required").build();
        }

        // Validate role
        if (request.role == null) {
            return Response.status(Response.Status.BAD_REQUEST).entity("Role is required").build();
        }

        if (!request.role.equals(Role.ADMIN) && !request.role.equals(Role.MEMBER)) {
            return Response.status(Response.Status.BAD_REQUEST).entity("Invalid role").build();
        }

        // Check if user already exists
        Optional<User> existingUser = store.findUser(request.email);
        if (existingUser.isPresent()) {
            User user = existingUser.get();
            if (user.tenantId != null && !user.tenantId.equals(tenantId)) {
                return Response.status(Response.Status.CONFLICT).entity("User is already invited to another tenant").build();
            }
            return Response.status(Response.Status.CONFLICT).entity("User already exists").build();
        }

        // Check if user is already invited to this tenant
        List<Invitation> existingInvitations = store.invitationsOfTenant(tenantId);
        for (Invitation invitation : existingInvitations) {
            if (invitation.email.equals(request.email)) {
                return Response.status(Response.Status.CONFLICT).entity("User is already invited").build();
            }
        }

        // Check if user is already active
        List<User> users = store.usersOfTenant(tenantId);
        for (User user : users) {
            if (user.email.equals(request.email) && user.status == UserStatus.ACTIVE) {
                return Response.status(Response. Status.CONFLICT).entity("User is already active").build();
            }
        }

        // Check if tenant has enough users
        Tenant tenant = store.tenants.get(tenantId);
        Plan plan = tenant.plan;
        if (plan == Plan.FREE) {
            int maxUsers = 1;
            if (plan.maxUsers != null) {
                maxUsers = plan.maxUsers;
            }
            int currentUsers = store.usersOfTenant(tenantId).size();
            if (currentUsers >= maxUsers) {
                return Response.status(Response.Status.PRECONDITION_FAILED).entity("Tenant has reached maximum number of users").build();
            }
        }

        // Create invitation
        String invitationId = UUID.randomUUID().toString();
        Instant now = Instant.now();
        Instant expiresAt = now.plus(Duration.ofHours(24)); // Invitation expires in 24 hours

        Invitation invitation = new Invitation();
        invitation.id = invitationId;
        invitation.tenantId = tenantId;
        invitation.email = request.email;
        invitation.role = request.role;
        invitation.createdAt = now;
        invitation.expiresAt = expiresAt;
        invitation.resendCount = 0;
        invitation.status = InvitationStatus.PENDING;

        store.invitations.put(invitationId, invitation);

        // Create audit log entry
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = request.actorId; // Assuming actorId is provided in the request
        audit.action = "CREATE_INVITATION";
        audit.targetId = invitationId;
        audit.timestamp = now;
        audit.details = "Invitation created for email: " + request.email + " with role: " + request.role;

        store.auditLog.add(audit);

        // Return 201 Created
        return Response.status(Response.Status.CREATED)
                .entity(new InvitationResponse(invitationId, expiresAt))
                .build();
    }

    // Helper class for request
    private static class InvitationRequest {
        public String email;
        public Role role;
        public String actorId; // Assuming actorId is provided in the request
    }

    // Helper class for response
    private static class InvitationResponse {
        public String id;
        public Instant expiresAt;

        public InvitationResponse(String id, Instant expiresAt) {
            this.id = id;
            this.expiresAt = expiresAt;
        }
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
sses
[INFO] 
[INFO] --- compiler:3.15.0:compile (default-compile) @ saas-users ---
[INFO] Recompiling the module because of changed source code.
[INFO] Compiling 10 source files with javac [debug release 21] to target/classes
[INFO] -------------------------------------------------------------
[ERROR] COMPILATION ERROR : 
[INFO] -------------------------------------------------------------
[ERROR] /work/baseline/t1/src/main/java/com/bench/api/InvitationResource.java:[74,9] cannot find symbol
  symbol:   class Tenant
  location: class com.bench.api.InvitationResource
[ERROR] /work/baseline/t1/src/main/java/com/bench/api/InvitationResource.java:[75,9] cannot find symbol
  symbol:   class Plan
  location: class com.bench.api.InvitationResource
[ERROR] /work/baseline/t1/src/main/java/com/bench/api/InvitationResource.java:[76,21] cannot find symbol
  symbol:   variable Plan
  location: class com.bench.api.InvitationResource
[INFO] 3 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  3.166 s
[INFO] Finished at: 2026-07-19T15:49:37Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/baseline/t1/src/main/java/com/bench/api/InvitationResource.java:[74,9] cannot find symbol
[ERROR]   symbol:   class Tenant
[ERROR]   location: class com.bench.api.InvitationResource
[ERROR] /work/baseline/t1/src/main/java/com/bench/api/InvitationResource.java:[75,9] cannot find symbol
[ERROR]   symbol:   class Plan
[ERROR]   location: class com.bench.api.InvitationResource
[ERROR] /work/baseline/t1/src/main/java/com/bench/api/InvitationResource.java:[76,21] cannot find symbol
[ERROR]   symbol:   variable Plan
[ERROR]   location: class com.bench.api.InvitationResource
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

FILE: src/main/java/com/bench/api/InvitationResource.java
```java
package com.bench.api;

import com.bench.model.Role;
import com.bench.model.Invitation;
import com.bench.model.InvitationStatus;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.model.Tenant;
import com.bench.model.Plan;
import com.bench.model.InvitationStatus;
import com.bench.model.AuditEntry;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.time.Instant;
import java.time.Duration;
import java.util.*;

@Path("/tenants/{tenantId}/invitations")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class InvitationResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response createInvitation(@PathParam("tenantId") String tenantId, InvitationRequest request) {
        // Validate tenant exists
        if (!store.tenants.containsKey(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).entity("Tenant not found").build();
        }

        // Validate email
        if (request.email == null || request.email.trim().isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST).entity("Email is required").build();
        }

        // Validate role
        if (request.role == null) {
            return Response.status(Response.Status.BAD_REQUEST).entity("Role is required").build();
        }

        if (!request.role.equals(Role.ADMIN) && !request.role.equals(Role.MEMBER)) {
            return Response.status(Response.Status.BAD_REQUEST).entity("Invalid role").build();
        }

        // Check if user already exists
        Optional<User> existingUser = store.findUser(request.email);
        if (existingUser.isPresent()) {
            User user = existingUser.get();
            if (user.tenantId != null && !user.tenantId.equals(tenantId)) {
                return Response.status(Response.Status.CONFLICT).entity("User is already invited to another tenant").build();
            }
            return Response.status(Response.Status.CONFLICT).entity("User already exists").build();
        }

        // Check if user is already invited to this tenant
        List<Invitation> existingInvitations = store.invitationsOfTenant(tenantId);
        for (Invitation invitation : existingInvitations) {
            if (invitation.email.equals(request.email)) {
                return Response.status(Response.Status.CONFLICT).entity("User is already invited").build();
            }
        }

        // Check if user is already active
        List<User> users = store.usersOfTenant(tenantId);
        for (User user : users) {
            if (user.email.equals(request.email) && user.status == UserStatus.ACTIVE) {
                return Response.status(Response.Status.CONFLICT).entity("User is already active").build();
            }
        }

        // Check if tenant has enough users
        Tenant tenant = store.tenants.get(tenantId);
        Plan plan = tenant.plan;
        if (plan == Plan.FREE) {
            int maxUsers = 1;
            if (plan.maxUsers != null) {
                maxUsers = plan.maxUsers;
            }
            int currentUsers = store.usersOfTenant(tenantId).size();
            if (currentUsers >= maxUsers) {
                return Response.status(Response.Status.PRECONDITION_FAILED).entity("Tenant has reached maximum number of users").build();
            }
        }

        // Create invitation
        String invitationId = UUID.randomUUID().toString();
        Instant now = Instant.now();
        Instant expiresAt = now.plus(Duration.ofHours(24)); // Invitation expires in 24 hours

        Invitation invitation = new Invitation();
        invitation.id = invitationId;
        invitation.tenantId = tenantId;
        invitation.email = request.email;
        invitation.role = request.role;
        invitation.createdAt = now;
        invitation.expiresAt = expiresAt;
        invitation.resendCount = 0;
        invitation.status = InvitationStatus.PENDING;

        store.invitations.put(invitationId, invitation);

        // Create audit log entry
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = request.actorId; // Assuming actorId is provided in the request
        audit.action = "CREATE_INVITATION";
        audit.targetId = invitationId;
        audit.timestamp = now;
        audit.details = "Invitation created for email: " + request.email + " with role: " + request.role;

        store.auditLog.add(audit);

        // Return 201 Created
        return Response.status(Response.Status.CREATED)
                .entity(new InvitationResponse(invitationId, expiresAt))
                .build();
    }

    // Helper class for request
    private static class InvitationRequest {
        public String email;
        public Role role;
        public String actorId; // Assuming actorId is provided in the request
    }

    // Helper class for response
    private static class InvitationResponse {
        public String id;
        public Instant expiresAt;

        public InvitationResponse(String id, Instant expiresAt) {
            this.id = id;
            this.expiresAt = expiresAt;
        }
    }
}
```