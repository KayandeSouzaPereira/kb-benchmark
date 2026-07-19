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


---

## assistant

FILE: src/main/java/com/bench/api/InvitationResendResource.java
```java
package com.bench.api;

import com.bench.model.Invitation;
import com.bench.model.InvitationStatus;
import com.bench.model.Role;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
public class InvitationResendResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response resendInvitation(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // 1. Validação do tenantId
        if (tenantId == null || tenantId.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST).entity("tenantId is required").build();
        }

        // 2. Validação do invitationId
        if (invitationId == null || invitationId.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST).entity("invitationId is required").build();
        }

        // 3. Verifica se o tenant existe
        Map<String, Tenant> tenants = store.tenants;
        if (!tenants.containsKey(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).entity("Tenant not found").build();
        }

        // 4. Verifica se o convite existe
        Map<String, Invitation> invitations = store.invitations;
        if (!invitations.containsKey(invitationId)) {
            return Response.status(Response. Status.NOT_FOUND).entity("Invitation not found").build();
        }

        Invitation invitation = invitations.get(invitationId);
        if (invitation.tenantId != null && !invitation.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).entity("Invitation belongs to a different tenant").build();
        }

        // 5. Verifica se o convite está em status válido para reenvio
        if (invitation.status != InvitationStatus.PENDING) {
            return Response.status(Response.Status.FORBIDDEN).entity("Invitation cannot be resent").build();
        }

        // 6. Verifica permissões do ator (X-Actor-Id)
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null) {
            return Response.status(Response.Status.FORBIDDEN).entity("Actor not found").build();
        }

        // 7. Verifica se o ator é um owner do tenant
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).entity("Actor is not a member of the tenant").build();
        }

        if (actor.status != UserStatus.ACTIVE) {
            return Response.status(Response.Status.FORBIDDEN).entity("Actor is not active").build();
        }

        // 8. Verifica se o ator tem permissão para reenviar convites
        if (!isUserAllowedToResendInvitation(actor, invitation)) {
            return Response.status(Response.Status.FORBIDDEN).entity("Actor is not allowed to resend invitation").build();
        }

        // 9. Incrementa o contador de reenvios
        invitation.resendCount++;

        // 10. Gera nova data de expiração (ex: 7 dias após a data de criação)
        Instant newExpiresAt = invitation.createdAt.plusDays(7);

        // 11. Atualiza o convite
        invitation.expiresAt = newExpiresAt;

        // 12. Registra a ação no audit log
        logAuditEntry(actorId, tenantId, invitationId, "resend_invitation");

        // 13. Retorna resposta
        return Response.ok()
                .entity(Map.of(
                        "resendCount", invitation.resendCount,
                        "expiresAt", invitation.expiresAt.toString()
                ))
                .build();
    }

    private boolean isUserAllowedToResendInvitation(User actor, Invitation invitation) {
        // Verifica se o ator é um owner do tenant
        if (actor.role == Role.OWNER) {
            return true;
        }

        // Verifica se o ator é um admin do tenant
        if (actor.role == Role.ADMIN) {
            return true;
        }

        // Verifica se o ator é um membro do tenant e o convite é para ele
        if (actor.role == Role.MEMBER && invitation.email.equals(actor.email)) {
            return true;
        }

        return false;
    }

    private void logAuditEntry(String actorId, String tenantId, String invitationId, String action) {
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = action;
        auditEntry.targetId = invitationId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "Resend invitation";

        store.auditLog.add(auditEntry);
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
  class Tenant
  location: class com.bench.api.InvitationResendResource
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/InvitationResendResource.java:[84,52] cannot find symbol
  symbol:   method plusDays(int)
  location: variable createdAt of type java.time.Instant
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/InvitationResendResource.java:[121,9] cannot find symbol
  symbol:   class AuditEntry
  location: class com.bench.api.InvitationResendResource
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/InvitationResendResource.java:[121,37] cannot find symbol
  symbol:   class AuditEntry
  location: class com.bench.api.InvitationResendResource
[INFO] 4 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.388 s
[INFO] Finished at: 2026-07-19T15:09:13Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/InvitationResendResource.java:[39,21] cannot find symbol
[ERROR]   symbol:   class Tenant
[ERROR]   location: class com.bench.api.InvitationResendResource
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/InvitationResendResource.java:[84,52] cannot find symbol
[ERROR]   symbol:   method plusDays(int)
[ERROR]   location: variable createdAt of type java.time.Instant
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/InvitationResendResource.java:[121,9] cannot find symbol
[ERROR]   symbol:   class AuditEntry
[ERROR]   location: class com.bench.api.InvitationResendResource
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/InvitationResendResource.java:[121,37] cannot find symbol
[ERROR]   symbol:   class AuditEntry
[ERROR]   location: class com.bench.api.InvitationResendResource
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

FILE: src/main/java/com/bench/api/InvitationResendResource.java
```java
package com.bench.api;

import com.bench.model.Invitation;
import com.bench.model.InvitationStatus;
import com.bench.model.Role;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.model.Tenant;
import com.bench.model.Plan;
import com.bench.model.InvitationStatus;
import com.bench.model.Role;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.model.Tenant;
import com.bench.model.Plan;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
public class InvitationResendResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response resendInvitation(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // 1. Validação do tenantId
        if (tenantId == null || tenantId.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST).entity("tenantId is required").build();
        }

        // 2. Validação do invitationId
        if (invitationId == null || invitationId.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST).entity("invitationId is required").build();
        }

        // 3. Verifica se o tenant existe
        Map<String, Tenant> tenants = store.tenants;
        if (!tenants.containsKey(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).entity("Tenant not found").build();
        }

        // 4. Verifica se o convite existe
        Map<String, Invitation> invitations = store.invitations;
        if (!invitations.containsKey(invitationId)) {
            return Response.status(Response.Status.NOT_FOUND).entity("Invitation not found").build();
        }

        Invitation invitation = invitations.get(invitationId);
        if (invitation.tenantId != null && !invitation.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).entity("Invitation belongs to a different tenant").build();
        }

        // 5. Verifica se o convite está em status válido para reenvio
        if (invitation.status != InvitationStatus.PENDING) {
            return Response.status(Response.Status.FORBIDDEN).entity("Invitation cannot be resent").build();
        }

        // 6. Verifica permissões do ator (X-Actor-Id)
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null) {
            return Response.status(Response.Status.FORBIDDEN).entity("Actor not found").build();
        }

        // 7. Verifica se o ator é um owner do tenant
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).entity("Actor is not a member of the tenant").build();
        }

        if (actor.status != UserStatus.ACTIVE) {
            return Response.status(Response.Status.FORBIDDEN).entity("Actor is not active").build();
        }

        // 8. Verifica se o ator tem permissão para reenviar convites
        if (!isUserAllowedToResendInvitation(actor, invitation)) {
            return Response.status(Response.Status.FORBIDDEN).entity("Actor is not allowed to resend invitation").build();
        }

        // 9. Incrementa o contador de reenvios
        invitation.resendCount++;

        // 10. Gera nova data de expiração (ex: 7 dias após a data de criação)
        Instant newExpiresAt = invitation.createdAt.plus(7, ChronoUnit.DAYS);

        // 11. Atualiza o convite
        invitation.expiresAt = newExpiresAt;

        // 12. Registra a ação no audit log
        logAuditEntry(actorId, tenantId, invitationId, "resend_invitation");

        // 13. Retorna resposta
        return Response.ok()
                .entity(Map.of(
                        "resendCount", invitation.resendCount,
                        "expiresAt", invitation.expiresAt.toString()
                ))
                .build();
    }

    private boolean isUserAllowedToResendInvitation(User actor, Invitation invitation) {
        // Verifica se o ator é um owner do tenant
        if (actor.role == Role.OWNER) {
            return true;
        }

        // Verifica se o ator é um admin do tenant
        if (actor.role == Role.ADMIN) {
            return true;
        }

        // Verifica se o ator é um membro do tenant e o convite é para ele
        if (actor.role == Role.MEMBER && invitation.email.equals(actor.email)) {
            return true;
        }

        return false;
    }

    private void logAuditEntry(String actorId, String tenantId, String invitationId, String action) {
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = action;
        auditEntry.targetId = invitationId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "Resend invitation";

        store.auditLog.add(auditEntry);
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
>------------------------
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
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/InvitationResendResource.java:[130,9] cannot find symbol
  symbol:   class AuditEntry
  location: class com.bench.api.InvitationResendResource
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/InvitationResendResource.java:[130,37] cannot find symbol
  symbol:   class AuditEntry
  location: class com.bench.api.InvitationResendResource
[INFO] 2 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.522 s
[INFO] Finished at: 2026-07-19T15:10:26Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/InvitationResendResource.java:[130,9] cannot find symbol
[ERROR]   symbol:   class AuditEntry
[ERROR]   location: class com.bench.api.InvitationResendResource
[ERROR] /work/baseline/t3/src/main/java/com/bench/api/InvitationResendResource.java:[130,37] cannot find symbol
[ERROR]   symbol:   class AuditEntry
[ERROR]   location: class com.bench.api.InvitationResendResource
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

FILE: src/main/java/com/bench/api/InvitationResendResource.java
```java
package com.bench.api;

import com.bench.model.Invitation;
import com.bench.model.InvitationStatus;
import com.bench.model.Role;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.model.Tenant;
import com.bench.model.AuditEntry;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
public class InvitationResendResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response resendInvitation(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // 1. Validação do tenantId
        if (tenantId == null || tenantId.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST).entity("tenantId is required").build();
        }

        // 2. Validação do invitationId
        if (invitationId == null || invitationId.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST).entity("invitationId is required").build();
        }

        // 3. Verifica se o tenant existe
        Map<String, Tenant> tenants = store.tenants;
        if (!tenants.containsKey(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).entity("Tenant not found").build();
        }

        // 4. Verifica se o convite existe
        Map<String, Invitation> invitations = store.invitations;
        if (!invitations.containsKey(invitationId)) {
            return Response.status(Response.Status.NOT_FOUND).entity("Invitation not found").build();
        }

        Invitation invitation = invitations.get(invitationId);
        if (invitation.tenantId != null && !invitation.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).entity("Invitation belongs to a different tenant").build();
        }

        // 5. Verifica se o convite está em status válido para reenvio
        if (invitation.status != InvitationStatus.PENDING) {
            return Response.status(Response.Status.FORBIDDEN).entity("Invitation cannot be resent").build();
        }

        // 6. Verifica permissões do ator (X-Actor-Id)
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null) {
            return Response.status(Response.Status.FORBIDDEN).entity("Actor not found").build();
        }

        // 7. Verifica se o ator é um owner do tenant
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).entity("Actor is not a member of the tenant").build();
        }

        if (actor.status != UserStatus.ACTIVE) {
            return Response.status(Response.Status.FORBIDDEN).entity("Actor is not active").build();
        }

        // 8. Verifica se o ator tem permissão para reenviar convites
        if (!isUserAllowedToResendInvitation(actor, invitation)) {
            return Response.status(Response.Status.FORBIDDEN).entity("Actor is not allowed to resend invitation").build();
        }

        // 9. Incrementa o contador de reenvios
        invitation.resendCount++;

        // 10. Gera nova data de expiração (ex: 7 dias após a data de criação)
        Instant newExpiresAt = invitation.createdAt.plus(7, ChronoUnit.DAYS);

        // 11. Atualiza o convite
        invitation.expiresAt = newExpiresAt;

        // 12. Registra a ação no audit log
        logAuditEntry(actorId, tenantId, invitationId, "resend_invitation");

        // 13. Retorna resposta
        return Response.ok()
                .entity(Map.of(
                        "resendCount", invitation.resendCount,
                        "expiresAt", invitation.expiresAt.toString()
                ))
                .build();
    }

    private boolean isUserAllowedToResendInvitation(User actor, Invitation invitation) {
        // Verifica se o ator é um owner do tenant
        if (actor.role == Role.OWNER) {
            return true;
        }

        // Verifica se o ator é um admin do tenant
        if (actor.role == Role.ADMIN) {
            return true;
        }

        // Verifica se o ator é um membro do tenant e o convite é para ele
        if (actor.role == Role.MEMBER && invitation.email.equals(actor.email)) {
            return true;
        }

        return false;
    }

    private void logAuditEntry(String actorId, String tenantId, String invitationId, String action) {
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = action;
        auditEntry.targetId = invitationId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "Resend invitation";

        store.auditLog.add(auditEntry);
    }
}
```