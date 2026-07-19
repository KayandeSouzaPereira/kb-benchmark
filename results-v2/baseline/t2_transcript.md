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

# Tarefa: excluir usuário

Implemente o endpoint de exclusão de usuário:

```
DELETE /tenants/{tenantId}/users/{userId}
Sucesso: 204 No Content
```

Implemente TODAS as regras de negócio, permissões, validações e convenções de
erro/auditoria que o time definiu para exclusão de usuários.


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

FILE: src/main/java/com/bench/api/UserResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;
import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(
        @PathParam("tenantId") String tenantId,
        @PathParam("userId") String userId,
        @HeaderParam("X-Actor-Id") String actorId
    ) {
        // 1. Validação de parâmetros
        if (tenantId == null || userId == null || actorId == null) {
            return Response.status(Response.Status.BAD_REQUEST).build();
        }

        // 2. Verifica se o usuário autenticado existe
        Optional<User> actorUserOpt = store.findUser(actorId);
        if (actorUserOpt.isEmpty()) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        User actorUser = actorUserOpt.get();

        // 3. Verifica se o usuário alvo existe
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User targetUser = targetUserOpt.get();

        // 4. Verifica se o usuário alvo pertence ao tenant
        if (!targetUser.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // 5. Verifica se o usuário alvo está ativo
        if (targetUser.status == UserStatus.DELETED) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // 6. Verifica se o usuário alvo está suspenso
        if (targetUser.status == UserStatus.SUSPENDED) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // 7. Verifica se o usuário autenticado é dono do tenant
        if (!actorUser.role.equals(Role.OWNER)) {
            // Verifica se o usuário autenticado é administrador do tenant
            if (!store.usersOfTenant(tenantId).stream()
                .anyMatch(user -> user.id.equals(actorId) && user.role == Role.ADMIN)) {
                return Response.status(Response.Status.FORBIDDEN).build();
            }
        }

        // 8. Verifica se o usuário alvo é o dono do tenant
        if (targetUser.role == Role.OWNER) {
            // Se o usuário alvo é o dono, só pode ser excluído se for o próprio dono
            if (!actorId.equals(targetUser.id)) {
                return Response.status(Response. Status.FORBIDDEN).build();
            }
        }

        // 9. Verifica se o plano do tenant permite a exclusão do usuário
        List<User> users = store.usersOfTenant(tenantId);
        long activeUsers = users.stream()
            .filter(user -> user.status == UserStatus.ACTIVE)
            .filter(user -> !user.id.equals(targetUser.id))
            .count();

        // Se o plano for FREE, o número máximo de usuários ativos é 1
        if (store.tenants.get(tenantId).plan == Plan.FREE && activeUsers >= 1) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // 10. Registra a ação no audit log
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "DELETE_USER";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "User deleted by " + actorId;

        store.auditLog.add(auditEntry);

        // 11. Marca o usuário como deletado
        targetUser.deletedAt = Instant.now();
        targetUser.status = UserStatus.DELETED;

        return Response.noContent().build();
    }
}
```