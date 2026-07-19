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

FILE: src/main/java/com/bench/api/UserRoleResource.java
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

@Path("/tenants/{tenantId}/users/{userId}/role")
public class UserRoleResource {

    @Inject
    InMemoryStore store;

    @PATCH
    public Response changeRole(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            RoleChangeRequest request) {
        
        // Validação do corpo da requisição
        if (request == null || request.role == null) {
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

        // Verifica se o usuário existe
        Optional<User> targetUserOpt = store.findUser(userId);
        if (!targetUserOpt.isPresent()) {
            return Response.status(404)
                    .entity(new ErrorResponse("User not found"))
                    .build();
        }
        User targetUser = targetUserOpt.get();

        // Verifica se o usuário pertence ao tenant
        if (!targetUser.tenantId.equals(tenantId)) {
            return Response.status(404)
                    .entity(new ErrorResponse("User not found in tenant"))
                    .build();
        }

        // Verifica permissões do ator
        if (!actor.id.equals(userId) && !canChangeRole(actor, targetUser, tenantId)) {
            return Response.status(403)
                    .entity(new ErrorResponse("Forbidden"))
                    .build();
        }

        // Verifica se o usuário está ativo
        if (targetUser.status == UserStatus.DELETED || targetUser.status == UserStatus.SUSPENDED) {
            return Response.status(400)
                    .entity(new ErrorResponse("Cannot change role of suspended or deleted user"))
                    .build();
        }

        // Verifica se a mudança de papel é válida
        if (!isValidRoleChange(actor, targetUser, request.role)) {
            return Response.status(422)
                    .entity(new ErrorResponse("Invalid role change"))
                    .build();
        }

        // Realiza a mudança de papel
        Role oldRole = targetUser.role;
        targetUser.role = request.role;

        // Registra auditoria
        logAudit(actor.id, tenantId, userId, "CHANGE_ROLE", 
                String.format("Role changed from %s to %s", oldRole, request.role));

        return Response.ok(targetUser).build();
    }

    private boolean canChangeRole(User actor, User targetUser, String tenantId) {
        // O ator deve ser OWNER ou ADMIN do tenant
        if (actor.role == Role.OWNER || actor.role == Role.ADMIN) {
            // Se o ator é OWNER ou ADMIN, pode mudar papel de qualquer usuário do mesmo tenant
            return actor.tenantId.equals(tenantId);
        }
        return false;
    }

    private boolean isValidRoleChange(User actor, User targetUser, Role newRole) {
        // Um OWNER não pode ser transformado em ADMIN ou MEMBER
        if (targetUser.role == Role.OWNER && newRole != Role.OWNER) {
            return false;
        }

        // Um ADMIN não pode ser transformado em OWNER
        if (targetUser.role == Role.ADMIN && newRole == Role.OWNER) {
            return false;
        }

        // Se o novo papel é MEMBER, é válido
        if (newRole == Role.MEMBER) {
            return true;
        }

        // Se o novo papel é ADMIN, é válido
        if (newRole == Role.ADMIN) {
            return true;
        }

        // Se o novo papel é OWNER, só pode ser feito por OWNER
        if (newRole == Role.OWNER && actor.role == Role.OWNER) {
            return true;
        }

        return false;
    }

    private String getActorId() {
        // Em uma implementação real, isso viria do header HTTP
        // Aqui estamos simulando com um valor fixo para testes
        return "actor-123";
    }

    private void logAudit(String actorId, String tenantId, String targetId, String action, String details) {
        AuditEntry entry = new AuditEntry();
        entry.id = UUID.randomUUID().toString();
        entry.tenantId = tenantId;
        entry.actorId = actorId;
        entry.action = action;
        entry.targetId = targetId;
        entry.timestamp = Instant.now();
        entry.details = details;
        store.auditLog.add(entry);
    }

    public static class RoleChangeRequest {
        public Role role;
    }

    public static class ErrorResponse {
        public String message;

        public ErrorResponse(String message) {
            this.message = message;
        }
    }
}
```