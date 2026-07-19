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
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {
        
        // Validação do ID do usuário autenticado
        if (actorId == null || actorId.isEmpty()) {
            return Response.status(401).entity("Unauthorized").build();
        }

        // Verifica se o usuário existe e está ativo
        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(401).entity("Unauthorized").build();
        }
        User actor = actorOpt.get();
        if (actor.status != UserStatus.ACTIVE) {
            return Response.status(403).entity("Forbidden").build();
        }

        // Verifica se o tenant existe
        Optional<Tenant> tenantOpt = store.tenants.values().stream()
                .filter(t -> t.id.equals(tenantId))
                .findFirst();
        if (!tenantOpt.isPresent()) {
            return Response.status(404).entity("Tenant not found").build();
        }
        Tenant tenant = tenantOpt.get();

        // Verifica se o usuário pertence ao tenant
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(403).entity("Forbidden").build();
        }

        // Verifica se o convite existe
        Optional<Invitation> invitationOpt = store.invitations.values().stream()
                .filter(i -> i.id.equals(invitationId) && i.tenantId.equals(tenantId))
                .findFirst();
        if (!invitationOpt.isPresent()) {
            return Response.status(404).entity("Invitation not found").build();
        }
        Invitation invitation = invitationOpt.get();

        // Verifica se o convite já foi aceito ou revogado
        if (invitation.status == InvitationStatus.ACCEPTED || 
            invitation.status == InvitationStatus.REVOKED) {
            return Response.status(422).entity("Cannot resend invitation: already accepted or revoked").build();
        }

        // Verifica se o convite expirou
        if (Instant.now().isAfter(invitation.expiresAt)) {
            return Response.status(410).entity("Invitation expired").build();
        }

        // Verifica permissões do usuário (deve ser OWNER ou ADMIN)
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return Response.status(403).entity("Forbidden").build();
        }

        // Verifica se o número de reenvios excedeu o limite
        // Supondo que o limite seja 5 reenvios
        if (invitation.resendCount >= 5) {
            return Response.status(422).entity("Maximum resend attempts reached").build();
        }

        // Atualiza o convite com novo resendCount e nova data de expiração
        invitation.resendCount++;
        invitation.expiresAt = Instant.now().plus(java.time.Duration.ofHours(24));

        // Cria entrada de auditoria
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "INVITATION_RESEND";
        auditEntry.targetId = invitationId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = String.format("Invitation resent. New expiration: %s", invitation.expiresAt);
        
        store.auditLog.add(auditEntry);

        // Retorna resposta com informações do convite reenviado
        ResendResponse response = new ResendResponse();
        response.resendCount = invitation.resendCount;
        response.expiresAt = invitation.expiresAt;

        return Response.ok(response).build();
    }

    public static class ResendResponse {
        public int resendCount;
        public Instant expiresAt;
    }
}
```