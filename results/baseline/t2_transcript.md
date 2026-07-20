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
            @PathParam("userId") String userId) {
        
        // Verificar se o usuário autenticado existe
        String actorId = getActorId();
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(401).build(); // Unauthorized
        }
        User actor = actorOpt.get();

        // Verificar se o tenant existe
        Optional<Tenant> tenantOpt = store.tenants.values().stream()
                .filter(t -> t.id.equals(tenantId))
                .findFirst();
        if (tenantOpt.isEmpty()) {
            return Response.status(404).build(); // Not Found
        }
        Tenant tenant = tenantOpt.get();

        // Verificar se o usuário a ser excluído existe
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return Response.status(404).build(); // Not Found
        }
        User targetUser = targetUserOpt.get();

        // Verificar se o usuário pertence ao tenant
        if (!targetUser.tenantId.equals(tenantId)) {
            return Response.status(404).build(); // Not Found - usuário não pertence ao tenant
        }

        // Verificar permissões do ator
        if (!actor.id.equals(userId) && !actor.role.equals(Role.OWNER) && !actor.role.equals(Role.ADMIN)) {
            return Response.status(403).build(); // Forbidden
        }

        // Verificar se o usuário é o único OWNER
        if (targetUser.role == Role.OWNER && store.countOwners(tenantId) <= 1) {
            return Response.status(422).entity("Cannot delete the last owner of the tenant").build();
        }

        // Verificar se o usuário já está excluído
        if (targetUser.status == UserStatus.DELETED) {
            return Response.status(410).build(); // Gone
        }

        // Excluir o usuário
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = Instant.now();
        
        // Definir data de purga (30 dias após exclusão)
        targetUser.purgeAt = targetUser.deletedAt.plus(java.time.Duration.ofDays(30));

        // Registrar auditoria
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = java.util.UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "DELETE_USER";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = String.format("User %s deleted by %s", userId, actorId);
        
        store.auditLog.add(auditEntry);

        return Response.noContent().build();
    }

    private String getActorId() {
        // Simulando a leitura do header X-Actor-Id
        // Em uma implementação real, isso seria feito com o framework de segurança
        // Por enquanto, estamos retornando um valor fixo para demonstração
        return "actor-user-id"; // Este valor deveria ser obtido do header HTTP
    }
}
```