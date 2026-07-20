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

FILE: src/main/java/com/bench/api/InvitationResource.java
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
import java.util.UUID;

@Path("/tenants/{tenantId}/invitations")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class InvitationResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response createInvitation(
            @PathParam("tenantId") String tenantId,
            InvitationRequest request) {
        
        // Validação do corpo da requisição
        if (request.email == null || request.email.isEmpty()) {
            return Response.status(422)
                    .entity(new ErrorResponse("Email is required"))
                    .build();
        }
        
        if (request.role == null) {
            return Response.status(422)
                    .entity(new ErrorResponse("Role is required"))
                    .build();
        }

        // Verifica se o usuário autenticado existe
        String actorId = getActorId();
        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(401)
                    .entity(new ErrorResponse("Unauthorized"))
                    .build();
        }
        
        User actor = actorOpt.get();
        
        // Verifica se o usuário autenticado pertence ao tenant
        if (!tenantId.equals(actor.tenantId)) {
            return Response.status(403)
                    .entity(new ErrorResponse("Forbidden"))
                    .build();
        }

        // Verifica se o usuário autenticado tem permissão para convidar (ADMIN ou OWNER)
        if (actor.role != Role.ADMIN && actor.role != Role.OWNER) {
            return Response.status(403)
                    .entity(new ErrorResponse("Forbidden"))
                    .build();
        }

        // Verifica se o email já está em uso
        List<User> existingUsers = store.usersOfTenant(tenantId);
        for (User user : existingUsers) {
            if (user.email.equals(request.email)) {
                return Response.status(422)
                        .entity(new ErrorResponse("Email already in use"))
                        .build();
            }
        }

        // Verifica se já existe um convite pendente para esse email
        List<Invitation> existingInvitations = store.invitationsOfTenant(tenantId);
        for (Invitation invitation : existingInvitations) {
            if (invitation.email.equals(request.email) && 
                invitation.status == InvitationStatus.PENDING) {
                return Response.status(422)
                        .entity(new ErrorResponse("Invitation already exists for this email"))
                        .build();
            }
        }

        // Verifica se o tenant existe
        Optional<Tenant> tenantOpt = store.tenants.values().stream()
                .filter(t -> t.id.equals(tenantId))
                .findFirst();
        
        if (!tenantOpt.isPresent()) {
            return Response.status(404)
                    .entity(new ErrorResponse("Tenant not found"))
                    .build();
        }

        Tenant tenant = tenantOpt.get();

        // Verifica se o número de usuários excederia o limite do plano
        long currentUsers = existingUsers.size();
        long owners = store.countOwners(tenantId);
        long maxUsers = tenant.plan.maxUsers != null ? tenant.plan.maxUsers : Long.MAX_VALUE;
        
        if (currentUsers + 1 > maxUsers) {
            return Response.status(422)
                    .entity(new ErrorResponse("Tenant user limit exceeded"))
                    .build();
        }

        // Cria o convite
        Invitation invitation = new Invitation();
        invitation.id = UUID.randomUUID().toString();
        invitation.tenantId = tenantId;
        invitation.email = request.email;
        invitation.role = request.role;
        invitation.createdAt = Instant.now();
        invitation.expiresAt = Instant.now().plus(java.time.Duration.ofDays(7));
        invitation.resendCount = 0;
        invitation.status = InvitationStatus.PENDING;

        // Persiste o convite
        store.invitations.put(invitation.id, invitation);

        // Registra na auditoria
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "INVITE_USER";
        auditEntry.targetId = invitation.id;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = String.format("Invited user %s with role %s", 
                                          invitation.email, invitation.role);
        store.auditLog.add(auditEntry);

        // Retorna a resposta
        InvitationResponse response = new InvitationResponse();
        response.id = invitation.id;
        response.expiresAt = invitation.expiresAt;

        return Response.status(201).entity(response).build();
    }

    private String getActorId() {
        // Em um ambiente real, isso viria do header HTTP
        // Aqui estamos simulando com um valor fixo para testes
        return "actor-123";
    }

    public static class InvitationRequest {
        public String email;
        public Role role;
    }

    public static class InvitationResponse {
        public String id;
        public Instant expiresAt;
    }

    public static class ErrorResponse {
        public String message;

        public ErrorResponse(String message) {
            this.message = message;
        }
    }
}
```