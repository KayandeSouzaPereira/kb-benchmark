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
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {
        
        // Validação do ID do usuário autenticado
        if (actorId == null || actorId.isEmpty()) {
            return Response.status(401).entity("Unauthorized").build();
        }

        // Verifica se o usuário existe
        Optional<User> actorOptional = store.findUser(actorId);
        if (!actorOptional.isPresent()) {
            return Response.status(401).entity("Unauthorized").build();
        }
        User actor = actorOptional.get();

        // Verifica se o usuário pertence ao tenant
        if (!tenantId.equals(actor.tenantId)) {
            return Response.status(403).entity("Forbidden").build();
        }

        // Verifica se o usuário tem permissão (deve ser OWNER ou ADMIN)
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return Response.status(403).entity("Forbidden").build();
        }

        // Busca o convite
        Invitation invitation = store.invitations.get(invitationId);
        if (invitation == null) {
            return Response.status(404).entity("Invitation not found").build();
        }

        // Verifica se o convite pertence ao tenant
        if (!tenantId.equals(invitation.tenantId)) {
            return Response.status(404).entity("Invitation not found").build();
        }

        // Verifica se o convite já foi aceito ou revogado
        if (invitation.status == InvitationStatus.ACCEPTED || 
            invitation.status == InvitationStatus.REVOKED) {
            return Response.status(422).entity("Cannot resend an accepted or revoked invitation").build();
        }

        // Verifica se o convite expirou
        if (Instant.now().isAfter(invitation.expiresAt)) {
            return Response.status(410).entity("Invitation expired").build();
        }

        // Atualiza o contador de reenvios
        invitation.resendCount += 1;

        // Atualiza a data de expiração (adiciona 7 dias)
        invitation.expiresAt = invitation.expiresAt.plus(java.time.Duration.ofDays(7));

        // Registra na auditoria
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "INVITATION_RESEND";
        auditEntry.targetId = invitationId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = String.format("Invitation resent. New expiration: %s", invitation.expiresAt);
        
        store.auditLog.add(auditEntry);

        // Retorna a resposta
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