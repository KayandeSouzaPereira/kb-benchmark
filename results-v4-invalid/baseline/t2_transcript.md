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

Armadilhas de API conhecidas:
- Para status HTTP fora do enum padrão (ex.: 422, 410), use
  `Response.status(422)` — `Response.Status` NÃO tem essas constantes.
- `Instant` não tem `plusHours`/`plusDays`; use
  `instant.plus(java.time.Duration.ofHours(n))`.


---

## assistant

FILE: src/main/java/com/bench/api/UserResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            @HeaderParam("X-Actor-Id") String actorId) {
        
        // 1. Validação do usuário autenticado
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(401).build();
        }
        User actor = actorOpt.get();

        // 2. Verificação se o usuário autenticado pertence ao tenant
        if (!tenantId.equals(actor.tenantId)) {
            return Response.status(403).build();
        }

        // 3. Busca pelo usuário a ser excluído
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return Response.status(404).build();
        }
        User targetUser = targetUserOpt.get();

        // 4. Verificação se o usuário pertence ao mesmo tenant
        if (!tenantId.equals(targetUser.tenantId)) {
            return Response.status(404).build();
        }

        // 5. Verificação de permissões (somente OWNER ou ADMIN podem excluir)
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return Response.status(403).build();
        }

        // 6. Verificação se o usuário a ser excluído é o próprio ator
        if (userId.equals(actorId)) {
            return Response.status(422).entity("Não é possível excluir o próprio usuário").build();
        }

        // 7. Verificação de regras de negócio para exclusão
        // Não pode haver menos de um OWNER no tenant
        if (targetUser.role == Role.OWNER && store.countOwners(tenantId) <= 1) {
            return Response.status(422).entity("Não é possível excluir o único OWNER do tenant").build();
        }

        // 8. Exclusão real do usuário
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = Instant.now();

        // 9. Definição de data de purga (30 dias após exclusão)
        targetUser.purgeAt = targetUser.deletedAt.plus(java.time.Duration.ofDays(30));

        // 10. Auditoria
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = java.util.UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "DELETE_USER";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "User deleted by " + actorId;

        store.auditLog.add(auditEntry);

        return Response.noContent().build();
    }
}
```