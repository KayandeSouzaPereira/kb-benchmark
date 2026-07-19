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
    public Response changeUserRole(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            @HeaderParam("X-Actor-Id") String actorId,
            Role newRole) {

        // Validação do novo papel
        if (newRole == null || !newRole.name().equals("OWNER") && !newRole.name().equals("ADMIN") && !newRole.name().equals("MEMBER")) {
            return Response.status(Response.Status.BAD_REQUEST).entity("Invalid role").build();
        }

        // Busca o usuário alvo
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).entity("User not found").build();
        }

        User user = userOpt.get();

        // Verifica se o usuário pertence ao tenant
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).entity("User not part of this tenant").build();
        }

        // Verifica se o usuário está ativo
        if (user.status == UserStatus.DELETED || user.status == UserStatus.SUSPENDED) {
            return Response.status(Response
                    .Status.FORBIDDEN)
                    .entity("User is deleted or suspended")
                    .build();
        }

        // Verifica se o usuário é o dono do tenant
        if (user.role == Role.OWNER) {
            return Response.status(Response.Status.FORBIDDEN)
                    .entity("Cannot change role of an OWNER")
                    .build();
        }

        // Verifica se o novo papel é válido para o tenant
        if (newRole == Role.OWNER) {
            // Só pode ser OWNER se o usuário for o único dono
            if (store.countOwners(tenantId) > 1) {
                return Response.status(Response.Status.FORBIDDEN)
                        .entity("Cannot promote to OWNER if there are multiple owners")
                        .build();
            }
        } else if (newRole == Role.ADMIN) {
            // Só pode ser ADMIN se o usuário não for OWNER
            if (user.role == Role.OWNER) {
                return Response.status(Response.Status.FORBIDDEN)
                        .entity("Cannot demote an OWNER to ADMIN")
                        .build();
            }
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
        auditEntry.details = String.format("User %s changed role from %s to %s", userId, user.role, newRole);
        store.auditLog.add(auditEntry);

        return Response.ok(user).build();
    }
}
```