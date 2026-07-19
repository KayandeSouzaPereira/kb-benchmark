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

# Tarefa: reenviar convite

Implemente o endpoint de reenvio de convite:

```
POST /tenants/{tenantId}/invitations/{invitationId}/resend
Sucesso: 200 com JSON { "resendCount": ..., "expiresAt": "..." }
```

Implemente TODAS as regras de negócio, permissões, validações e convenções de
erro/auditoria que o time definiu para reenvio de convites.


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

FILE: src/main/java/com/bench/api/ResendInvitationResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;
import jakarta.ws.rs.core.MediaType;
import java.time.Instant;
import java.time.Duration;
import java.util.Optional;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
public class ResendInvitationResource {

    @Inject
    InMemoryStore store;

    @Context
    UriInfo uriInfo;

    @Context
    SecurityContext securityContext;

    @POST
    public Response resendInvitation(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Verificar se o usuário autenticado existe
        Optional<User> actor = store.findUser(actorId);
        if (actor.isEmpty()) {
            return Response.status(Response.Status.UNAUTHORIZED).build();
        }

        // Verificar se o tenant existe
        Optional<Tenant> tenantOpt = store.tenants.get(tenantId);
        if (tenantOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        Tenant tenant = tenantOpt.get();

        // Verificar se o convite existe
        Optional<Invitation> invitationOpt = store.invitations.get(invitationId);
        if (invitationOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        Invitation invitation = invitationOpt.get();

        // Verificar permissões: o usuário deve ser dono do tenant ou ter permissão para reenviar convites
        if (!isAllowedToResendInvitation(actor.get(), tenantId, invitation)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // Verificar se o convite está em status válido para reenvio
        if (invitation.status != InvitationStatus.PENDING) {
            return Response.status(Response.Status.BAD_REQUEST).build();
        }

        // Verificar se o convite expirou
        if (invitation.expiresAt.isBefore(Instant.now())) {
            return Response.status(Response.Status.GONE).build();
        }

        // Incrementar o contador de reenvios
        int newResendCount = invitation.resendCount + 1;

        // Atualizar a data de expiração do convite
        Instant newExpiresAt = invitation.expiresAt.plus(Duration.ofHours(24));

        // Atualizar o convite
        Invitation updatedInvitation = new Invitation(
                invitation.id,
                invitation.tenantId,
                invitation.email,
                invitation.role,
                invitation.createdAt,
                newExpiresAt,
                newResendCount,
                invitation.status
        );

        store.invitations.put(invitationId, updatedInvitation);

        // Registrar auditoria
        AuditEntry auditEntry = new AuditEntry(
                java.time.Instant.now().toString(),
                tenantId,
                actorId,
                "invitation_resend",
                invitationId,
                "Resend invitation with ID " + invitationId + " for tenant " + tenantId
        );

        store.auditLog.add(auditEntry);

        // Retornar resposta
        return Response.ok(new ResendInvitationResponse(
                newResendCount,
                newExpiresAt.toString()
        )).build();
    }

    private boolean isAllowedToResendInvitation(User actor, String tenantId, Invitation invitation) {
        // Verificar se o usuário é dono do tenant
        if (store.countOwners(tenantId) > 0) {
            // Verificar se o usuário é dono do tenant
            List<User> users = store.usersOfTenant(tenantId);
            return users.stream()
                    .anyMatch(user -> user.status != UserStatus.DELETED && user.role == Role.OWNER && user.id.equals(actor.id));
        }

        // Se o usuário não é dono, verificar se ele é um membro ativo do tenant
        List<User> users = store.usersOfTenant(tenantId);
        return users.stream()
                .anyMatch(user -> user.status == UserStatus.ACTIVE && user.id.equals(actor.id));
    }
}

class ResendInvitationResponse {
    public final int resendCount;
    public final String expiresAt;

    public ResendInvitationResponse(int resendCount, String expiresAt) {
        this.resendCount = resend
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
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[131,34] reached end of file while parsing
[INFO] 1 error
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.063 s
[INFO] Finished at: 2026-07-19T15:55:11Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[131,34] reached end of file while parsing
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

FILE: src/main/java/com/bench/api/ResendInvitationResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;
import jakarta.ws.rs.core.MediaType;
import java.time.Instant;
import java.time.Duration;
import java.util.Optional;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
public class ResendInvitationResource {

    @Inject
    InMemoryStore store;

    @Context
    UriInfo uriInfo;

    @Context
    SecurityContext securityContext;

    @POST
    public Response resendInvitation(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Verificar se o usuário autenticado existe
        Optional<User> actor = store.findUser(actorId);
        if (actor.isEmpty()) {
            return Response.status(Response.Status.UNAUTHORIZED).build();
        }

        // Verificar se o tenant existe
        Optional<Tenant> tenantOpt = store.tenants.get(tenantId);
        if (tenantOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        Tenant tenant = tenantOpt.get();

        // Verificar se o convite existe
        Optional<Invitation> invitationOpt = store.invitations.get(invitationId);
        if (invitationOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        Invitation invitation = invitationOpt.get();

        // Verificar permissões: o usuário deve ser dono do tenant ou ter permissão para reenviar convites
        if (!isAllowedToResendInvitation(actor.get(), tenantId, invitation)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // Verificar se o convite está em status válido para reenvio
        if (invitation.status != InvitationStatus.PENDING) {
            return Response.status(Response.Status.BAD_REQUEST).build();
        }

        // Verificar se o convite expirou
        if (invitation.expiresAt.isBefore(Instant.now())) {
            return Response.status(Response.Status.GONE).build();
        }

        // Incrementar o contador de reenvios
        int newResendCount = invitation.resendCount + 1;

        // Atualizar a data de expiração do convite
        Instant newExpiresAt = invitation.expiresAt.plus(Duration.ofHours(24));

        // Atualizar o convite
        Invitation updatedInvitation = new Invitation(
                invitation.id,
                invitation.tenantId,
                invitation.email,
                invitation.role,
                invitation.createdAt,
                newExpiresAt,
                newResendCount,
                invitation.status
        );

        store.invitations.put(invitationId, updatedInvitation);

        // Registrar auditoria
        AuditEntry auditEntry = new AuditEntry(
                java.time.Instant.now().toString(),
                tenantId,
                actorId,
                "invitation_resend",
                invitationId,
                "Resend invitation with ID " + invitationId + " for tenant " + tenantId
        );

        store.auditLog.add(auditEntry);

        // Retornar resposta
        return Response.ok(new ResendInvitationResponse(
                newResendCount,
                newExpiresAt.toString()
        )).build();
    }

    private boolean isAllowedToResendInvitation(User actor, String tenantId, Invitation invitation) {
        // Verificar se o usuário é dono do tenant
        if (store.countOwners(tenantId) > 0) {
            // Verificar se o usuário é dono do tenant
            List<User> users = store.usersOfTenant(tenantId);
            return users.stream()
                    .anyMatch(user -> user.status != UserStatus.DELETED && user.role == Role.OWNER && user.id.equals(actor.id));
        }

        // Se o usuário não é dono, verificar se ele é um membro ativo do tenant
        List<User> users = store.usersOfTenant(tenantId);
        return users.stream()
                .anyMatch(user -> user.status == UserStatus.ACTIVE && user.id.equals(actor.id));
    }
}

class ResendInvitationResponse {
    public final int resendCount;
    public final String expiresAt;

    public ResendInvitationResponse(int resendCount, String expiresAt) {
        this.resendCount = resendCount;
        this.expiresAt = expiresAt;
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
h.model.AuditEntry cannot be applied to given types;
  required: no arguments
  found:    java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String
  reason: actual and formal argument lists differ in length
[INFO] 4 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.421 s
[INFO] Finished at: 2026-07-19T15:56:09Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[41,55] incompatible types: com.bench.model.Tenant cannot be converted to java.util.Optional<com.bench.model.Tenant>
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[49,67] incompatible types: com.bench.model.Invitation cannot be converted to java.util.Optional<com.bench.model.Invitation>
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[78,40] constructor Invitation in class com.bench.model.Invitation cannot be applied to given types;
[ERROR]   required: no arguments
[ERROR]   found:    java.lang.String,java.lang.String,java.lang.String,com.bench.model.Role,java.time.Instant,java.time.Instant,int,com.bench.model.InvitationStatus
[ERROR]   reason: actual and formal argument lists differ in length
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[92,33] constructor AuditEntry in class com.bench.model.AuditEntry cannot be applied to given types;
[ERROR]   required: no arguments
[ERROR]   found:    java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String
[ERROR]   reason: actual and formal argument lists differ in length
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

FILE: src/main/java/com/bench/api/ResendInvitationResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;
import jakarta.ws.rs.core.MediaType;
import java.time.Instant;
import java.time.Duration;
import java.util.Optional;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
public class ResendInvitationResource {

    @Inject
    InMemoryStore store;

    @Context
    UriInfo uriInfo;

    @Context
    SecurityContext securityContext;

    @POST
    public Response resendInvitation(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Verificar se o usuário autenticado existe
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(Response.Status.UNAUTHORIZED).build();
        }

        User actor = actorOpt.get();

        // Verificar se o tenant existe
        Optional<Tenant> tenantOpt = Optional.ofNullable(store.tenants.get(tenantId));
        if (tenantOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        Tenant tenant = tenantOpt.get();

        // Verificar se o convite existe
        Optional<Invitation> invitationOpt = Optional.ofNullable(store.invitations.get(invitationId));
        if (invitationOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        Invitation invitation = invitationOpt.get();

        // Verificar permissões: o usuário deve ser dono do tenant ou ter permissão para reenviar convites
        if (!isAllowedToResendInvitation(actor, tenantId, invitation)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // Verificar se o convite está em status válido para reenvio
        if (invitation.status != InvitationStatus.PENDING) {
            return Response.status(Response.Status.BAD_REQUEST).build();
        }

        // Verificar se o convite expirou
        if (invitation.expiresAt.isBefore(Instant.now())) {
            return Response.status(Response.Status.GONE).build();
        }

        // Incrementar o contador de reenvios
        int newResendCount = invitation.resendCount + 1;

        // Atualizar a data de expiração do convite
        Instant newExpiresAt = invitation.expiresAt.plus(Duration.ofHours(24));

        // Atualizar o convite
        Invitation updatedInvitation = new Invitation(
                invitation.id,
                invitation.tenantId,
                invitation.email,
                invitation.role,
                invitation.createdAt,
                newExpiresAt,
                newResendCount,
                invitation.status
        );

        store.invitations.put(invitationId, updatedInvitation);

        // Registrar auditoria
        AuditEntry auditEntry = new AuditEntry(
                java.time.Instant.now(),
                tenantId,
                actorId,
                "invitation_resend",
                invitationId,
                "Resend invitation with ID " + invitationId + " for tenant " + tenantId
        );

        store.auditLog.add(auditEntry);

        // Retornar resposta
        return Response.ok(new ResendInvitationResponse(
                newResendCount,
                newExpiresAt.toString()
        )).build();
    }

    private boolean isAllowedToResendInvitation(User actor, String tenantId, Invitation invitation) {
        // Verificar se o usuário é dono do tenant
        if (store.countOwners(tenantId) > 0) {
            // Verificar se o usuário é dono do tenant
            List<User> users = store.usersOfTenant(tenantId);
            return users.stream()
                    .anyMatch(user -> user.status != UserStatus.DELETED && user.role == Role.OWNER && user.id.equals(actor.id));
        }

        // Se o usuário não é dono, verificar se ele é um membro ativo do tenant
        List<User> users = store.usersOfTenant(tenantId);
        return users.stream()
                .anyMatch(user -> user.status == UserStatus.ACTIVE && user.id.equals(actor.id));
    }
}

class ResendInvitationResponse {
    public final int resendCount;
    public final String expiresAt;

    public ResendInvitationResponse(int resendCount, String expiresAt) {
        this.resendCount = resendCount;
        this.expiresAt = expiresAt;
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
cannot be applied to given types;
  required: no arguments
  found:    java.lang.String,java.lang.String,java.lang.String,com.bench.model.Role,java.time.Instant,java.time.Instant,int,com.bench.model.InvitationStatus
  reason: actual and formal argument lists differ in length
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[94,33] constructor AuditEntry in class com.bench.model.AuditEntry cannot be applied to given types;
  required: no arguments
  found:    java.time.Instant,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String
  reason: actual and formal argument lists differ in length
[INFO] 2 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.559 s
[INFO] Finished at: 2026-07-19T15:57:15Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[80,40] constructor Invitation in class com.bench.model.Invitation cannot be applied to given types;
[ERROR]   required: no arguments
[ERROR]   found:    java.lang.String,java.lang.String,java.lang.String,com.bench.model.Role,java.time.Instant,java.time.Instant,int,com.bench.model.InvitationStatus
[ERROR]   reason: actual and formal argument lists differ in length
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[94,33] constructor AuditEntry in class com.bench.model.AuditEntry cannot be applied to given types;
[ERROR]   required: no arguments
[ERROR]   found:    java.time.Instant,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String
[ERROR]   reason: actual and formal argument lists differ in length
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

FILE: src/main/java/com/bench/api/ResendInvitationResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;
import jakarta.ws.rs.core.MediaType;
import java.time.Instant;
import java.time.Duration;
import java.util.Optional;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
public class ResendInvitationResource {

    @Inject
    InMemoryStore store;

    @Context
    UriInfo uriInfo;

    @Context
    SecurityContext securityContext;

    @POST
    public Response resendInvitation(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Verificar se o usuário autenticado existe
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(Response.Status.UNAUTHORIZED).build();
        }

        User actor = actorOpt.get();

        // Verificar se o tenant existe
        Optional<Tenant> tenantOpt = Optional.ofNullable(store.tenants.get(tenantId));
        if (tenantOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        Tenant tenant = tenantOpt.get();

        // Verificar se o convite existe
        Optional<Invitation> invitationOpt = Optional.ofNullable(store.invitations.get(invitationId));
        if (invitationOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        Invitation invitation = invitationOpt.get();

        // Verificar permissões: o usuário deve ser dono do tenant ou ter permissão para reenviar convites
        if (!isAllowedToResendInvitation(actor, tenantId, invitation)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // Verificar se o convite está em status válido para reenvio
        if (invitation.status != InvitationStatus.PENDING) {
            return Response.status(Response.Status.BAD_REQUEST).build();
        }

        // Verificar se o convite expirou
        if (invitation.expiresAt.isBefore(Instant.now())) {
            return Response.status(Response.Status.GONE).build();
        }

        // Incrementar o contador de reenvios
        int newResendCount = invitation.resendCount + 1;

        // Atualizar a data de expiração do convite
        Instant newExpiresAt = invitation.expiresAt.plus(Duration.ofHours(24));

        // Atualizar o convite
        Invitation updatedInvitation = new Invitation(
                invitation.id,
                invitation.tenantId,
                invitation.email,
                invitation.role,
                invitation.createdAt,
                newExpiresAt,
                newResendCount,
                invitation.status
        );

        store.invitations.put(invitationId, updatedInvitation);

        // Registrar auditoria
        AuditEntry auditEntry = new AuditEntry(
                java.time.Instant.now(),
                tenantId,
                actorId,
                "invitation_resend",
                invitationId,
                "Resend invitation with ID " + invitationId + " for tenant " + tenantId
        );

        store.auditLog.add(auditEntry);

        // Retornar resposta
        return Response.ok(new ResendInvitationResponse(
                newResendCount,
                newExpiresAt.toString()
        )).build();
    }

    private boolean isAllowedToResendInvitation(User actor, String tenantId, Invitation invitation) {
        // Verificar se o usuário é dono do tenant
        if (store.countOwners(tenantId) > 0) {
            // Verificar se o usuário é dono do tenant
            List<User> users = store.usersOfTenant(tenantId);
            return users.stream()
                    .anyMatch(user -> user.status != UserStatus.DELETED && user.role == Role.OWNER && user.id.equals(actor.id));
        }

        // Se o usuário não é dono, verificar se ele é um membro ativo do tenant
        List<User> users = store.usersOfTenant(tenantId);
        return users.stream()
                .anyMatch(user -> user.status == UserStatus.ACTIVE && user.id.equals(actor.id));
    }
}

class ResendInvitationResponse {
    public final int resendCount;
    public final String expiresAt;

    public ResendInvitationResponse(int resendCount, String expiresAt) {
        this.resendCount = resendCount;
        this.expires
```