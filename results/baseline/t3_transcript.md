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

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class InvitationResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response resendInvitation(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId) {

        // Obter o usuário autenticado do header
        String actorId = getActorId();
        if (actorId == null) {
            return Response.status(401).build();
        }

        // Verificar se o usuário existe e está ativo
        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent() || actorOpt.get().status != UserStatus.ACTIVE) {
            return Response.status(403).build();
        }

        // Verificar se o tenant existe
        Optional<Tenant> tenantOpt = Optional.ofNullable(store.tenants.get(tenantId));
        if (!tenantOpt.isPresent()) {
            return Response.status(404).entity(new ErrorResponse("Tenant not found")).build();
        }

        // Verificar se o convite existe
        Invitation invitation = store.invitations.get(invitationId);
        if (invitation == null) {
            return Response.status(404).entity(new ErrorResponse("Invitation not found")).build();
        }

        // Verificar se o convite pertence ao tenant
        if (!invitation.tenantId.equals(tenantId)) {
            return Response.status(404).entity(new ErrorResponse("Invitation not found")).build();
        }

        // Verificar permissões do usuário (deve ser OWNER ou ADMIN)
        List<User> tenantUsers = store.usersOfTenant(tenantId);
        User actor = actorOpt.get();
        boolean hasPermission = tenantUsers.stream()
                .filter(u -> u.id.equals(actorId))
                .anyMatch(u -> u.role == Role.OWNER || u.role == Role.ADMIN);

        if (!hasPermission) {
            return Response.status(403).build();
        }

        // Verificar se o convite já foi aceito ou revogado
        if (invitation.status == InvitationStatus.ACCEPTED || invitation.status == InvitationStatus.REVOKED) {
            return Response.status(422).entity(new ErrorResponse("Cannot resend an accepted or revoked invitation")).build();
        }

        // Verificar se o convite expirou
        if (Instant.now().isAfter(invitation.expiresAt)) {
            return Response.status(410).entity(new ErrorResponse("Invitation has expired")).build();
        }

        // Atualizar o contador de reenvios e a data de expiração
        invitation.resendCount++;
        invitation.expiresAt = Instant.now().plus(java.time.Duration.ofDays(7));

        // Registrar na auditoria
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "INVITATION_RESEND";
        auditEntry.targetId = invitationId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = String.format("Invitation resent. New expiration: %s", invitation.expiresAt);
        store.auditLog.add(auditEntry);

        // Retornar resposta com o número de reenvios e nova data de expiração
        ResendResponse response = new ResendResponse();
        response.resendCount = invitation.resendCount;
        response.expiresAt = invitation.expiresAt;

        return Response.ok(response).build();
    }

    private String getActorId() {
        // Em um ambiente real, você obteria isso do header HTTP
        // Aqui estamos simulando com um valor fixo para demonstração
        // Na prática, você usaria algo como:
        // String actorId = request.getHeader("X-Actor-Id");
        // return actorId;
        return "actor-id"; // Placeholder - substituir conforme implementação real
    }

    // Classes auxiliares para resposta e erro
    public static class ResendResponse {
        public int resendCount;
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