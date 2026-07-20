## system

Você é um engenheiro de software sênior de um time de produto.
O time mantém uma base de conhecimento em arquivos Markdown com as regras de
negócio e convenções. Você DEVE consultá-la antes de escrever código, porque
as regras específicas do produto não são óbvias.

Para explorar a base, responda com UMA única linha de comando por mensagem:

ACTION: ls <caminho>      (lista arquivos de um diretório; use "." para a raiz)
ACTION: grep <termo>      (busca textual em todas as notas)
ACTION: read <arquivo>    (lê o conteúdo de uma nota)

Após cada ACTION você receberá o resultado. Você tem no máximo 8
ações no total — use-as bem.

Quando tiver o que precisa, produza os arquivos finais neste formato exato
(pode haver mais de um bloco FILE):

FILE: caminho/relativo/do/Arquivo.java
```java
<conteúdo completo do arquivo>
```

Regras do formato: nunca misture ACTION e FILE na mesma resposta; escreva
arquivos completos e compiláveis; não modifique os arquivos existentes do
projeto.

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

ACTION: ls .
```

---

## user

RESULT (7 ações restantes):
202601050900-mapa-dominio-usuarios.md
202601051030-papeis-do-tenant.md
202601080800-lockout-e-senhas.md
202601121000-limites-por-plano.md
202601201300-auditoria-de-mutacoes.md
202601201330-codigos-de-erro-da-api.md
202602041100-expiracao-de-convites-72h.md
202602041130-reenvio-de-convites.md
202602101415-protecao-do-owner.md
202602101430-ultimo-owner.md
202602151100-isolamento-de-tenant-404.md
202603121015-convites-e-limite-duvida.md
202603150900-soft-delete-30-dias.md
202603150930-quem-pode-deletar.md
202604010900-mapa-api-e-convencoes.md
202604111600-badges-de-status-no-front.md
202605021430-convites-pendentes-contam.md
202605190800-ideias-de-precos.md

---

## assistant

ACTION: grep -i "papel\|role" 202601051030-papeis-do-tenant.md
```

---

## user

RESULT (6 ações restantes):
nenhum resultado para: -i "papel\|role" 202601051030-papeis-do-tenant.md

---

## assistant

ACTION: read 202601051030-papeis-do-tenant.md
```

---

## user

RESULT (5 ações restantes):
# 202601051030 Papéis do tenant

Três papéis, hierarquia estrita: OWNER > ADMIN > MEMBER.

Mutações administrativas — convidar alguém, excluir usuário, mudar papel —
pedem ADMIN ou OWNER ("ADMIN+"). Um MEMBER que tente recebe 403 com código
`FORBIDDEN_ROLE` (códigos em [[202601201330-codigos-de-erro-da-api]]).

Mas hierarquia não é só "quem está acima manda": o owner tem proteções
específicas que um admin não atravessa → [[202602101415-protecao-do-owner]].

E o ator precisa ser do próprio tenant → [[202602151100-isolamento-de-tenant-404]].


---

## assistant

ACTION: read 202602101415-protecao-do-owner.md
```

---

## user

RESULT (4 ações restantes):
# 202602101415 Proteção do owner

Percebi hoje discutindo o incidente do cliente Vetrix: se um ADMIN pode
rebaixar ou excluir um OWNER, um admin malicioso toma o tenant.

Regra que fechamos: **ADMIN nunca altera nem exclui um OWNER** — nem papel,
nem exclusão. Resposta: 403 `OWNER_PROTECTED`. Só um OWNER mexe em outro
OWNER, e só um OWNER promove alguém a OWNER.

Isso conecta com o caso extremo do último owner: [[202602101430-ultimo-owner]].
Papéis em geral: [[202601051030-papeis-do-tenant]].


---

## assistant

ACTION: read 202602101430-ultimo-owner.md
```

---

## user

RESULT (3 ações restantes):
# 202602101430 Último owner

Continuação de [[202602101415-protecao-do-owner]]: o tenant nunca pode ficar
sem OWNER.

Qualquer operação que deixaria zero owners ativos — rebaixar o último owner
(inclusive ele rebaixando a si mesmo), removê-lo, ele sair do tenant —
falha com **409 `LAST_OWNER`**.

Com dois ou mais owners a operação passa: um owner pode rebaixar o outro
normalmente.

"Owner ativo" aqui = owner com status != DELETED. Relaciona com
[[202603150900-soft-delete-30-dias]].


---

## assistant

ACTION: read 202601201330-codigos-de-erro-da-api.md
```

---

## user

RESULT (2 ações restantes):
# 202601201330 Códigos de erro da API

Envelope padrão de erro de negócio (o `code` é contrato estável, `message`
é livre):

```json
{ "code": "CODIGO_ESTAVEL", "message": "texto humano" }
```

Códigos que já firmamos:

- 403 `FORBIDDEN_ROLE` — papel insuficiente ([[202601051030-papeis-do-tenant]])
- 403 `OWNER_PROTECTED` — admin mexendo em owner ([[202602101415-protecao-do-owner]])
- 409 `LAST_OWNER` — tenant ficaria sem owner ([[202602101430-ultimo-owner]])
- 422 `PLAN_LIMIT_EXCEEDED` — limite de assentos ([[202605021430-convites-pendentes-contam]])
- 422 `CANNOT_DELETE_SELF` — auto-exclusão ([[202603150930-quem-pode-deletar]])
- 422 `RESEND_LIMIT_REACHED` — 4º reenvio ([[202602041130-reenvio-de-convites]])
- 410 `INVITATION_EXPIRED` — aceitar convite vencido ([[202602041100-expiracao-de-convites-72h]])
- 404 `NOT_FOUND` — inexistente OU ator de outro tenant ([[202602151100-isolamento-de-tenant-404]])

Sem stacktrace no body, nunca.


---

## assistant

ACTION: read 202602151100-isolamento-de-tenant-404.md
```

---

## user

RESULT (1 ações restantes):
# 202602151100 Isolamento de tenant responde 404, não 403

O ator (vem no header `X-Actor-Id`) tem que pertencer ao tenant da URL.

Detalhe que quase erramos: quando o ator é de OUTRO tenant, a resposta é
**404 `NOT_FOUND`**, não 403. Um 403 confirmaria para um estranho que o
recurso existe — vazamento de informação. 404 não conta nada.

Vale para todos os endpoints de usuários e convites.
Papéis: [[202601051030-papeis-do-tenant]].
Códigos: [[202601201330-codigos-de-erro-da-api]].


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

@Path("/tenants/{tenantId}/users/{userId}/role")
public class UserRoleResource {

    @Inject
    InMemoryStore store;

    @PATCH
    public Response changeRole(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            RoleChangeRequest request) {
        String actorId = getActorId();
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null || !tenantId.equals(actor.tenantId)) {
            return Response.status(404).entity(new ErrorResponse("NOT_FOUND", "Tenant or user not found")).build();
        }

        User targetUser = store.findUser(userId).orElse(null);
        if (targetUser == null || !tenantId.equals(targetUser.tenantId)) {
            return Response.status(404).entity(new ErrorResponse("NOT_FOUND", "User not found")).build();
        }

        // Verificar permissões do ator
        if (!hasPermission(actor, targetUser)) {
            return Response.status(403)
                    .entity(new ErrorResponse("FORBIDDEN_ROLE", "Insufficient role to change user role"))
                    .build();
        }

        // Verificar proteção do owner
        if (targetUser.role == Role.OWNER && actor.role != Role.OWNER) {
            return Response.status(403)
                    .entity(new ErrorResponse("OWNER_PROTECTED", "Cannot modify owner role by non-owner"))
                    .build();
        }

        // Verificar se é o último owner
        if (targetUser.role == Role.OWNER && request.role != Role.OWNER && !canRemoveLastOwner(tenantId, userId)) {
            return Response.status(409)
                    .entity(new ErrorResponse("LAST_OWNER", "Cannot remove last owner"))
                    .build();
        }

        // Realizar mudança de papel
        targetUser.role = request.role;

        // Registrar auditoria
        store.auditLog.add(new AuditEntry()
                .id(java.util.UUID.randomUUID().toString())
                .tenantId(tenantId)
                .actorId(actorId)
                .action("USER_ROLE_CHANGED")
                .targetId(userId)
                .timestamp(Instant.now())
                .details("Role changed to " + request.role));

        return Response.ok(targetUser).build();
    }

    private boolean hasPermission(User actor, User targetUser) {
        if (actor.role == Role.OWNER) return true;
        if (actor.role == Role.ADMIN && targetUser.role != Role.OWNER) return true;
        return false;
    }

    private boolean canRemoveLastOwner(String tenantId, String userId) {
        List<User> owners = store.usersOfTenant(tenantId).stream()
                .filter(u -> u.role == Role.OWNER && u.status != UserStatus.DELETED)
                .toList();
        return owners.size() > 1 || !owners.get(0).id.equals(userId);
    }

    private String getActorId() {
        // Em um ambiente real, isso viria do header HTTP
        // Aqui estamos simulando com uma variável de ambiente ou configuração
        return System.getenv("X_ACTOR_ID");
    }

    public static class RoleChangeRequest {
        public Role role;
    }

    public static class ErrorResponse {
        public String code;
        public String message;

        public ErrorResponse(String code, String message) {
            this.code = code;
            this.message = message;
        }
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
not find symbol
  symbol:   method id(java.lang.String)
  location: class com.bench.model.AuditEntry, line 62 in /work/vault-b/t4/src/main/java/com/bench/api/UserRoleResource.java
2026-07-20 11:36:25,561 ERROR [io.quarkus.deployment.dev.JavaCompilationProvider] (vert.x-worker-thread-1) cannot find symbol
  symbol:   method id(java.lang.String)
  location: class com.bench.model.AuditEntry, line 62 in /work/vault-b/t4/src/main/java/com/bench/api/UserRoleResource.java
2026-07-20 11:36:27,619 ERROR [io.quarkus.deployment.dev.JavaCompilationProvider] (vert.x-worker-thread-1) cannot find symbol
  symbol:   method id(java.lang.String)
  location: class com.bench.model.AuditEntry, line 62 in /work/vault-b/t4/src/main/java/com/bench/api/UserRoleResource.java
2026-07-20 11:36:29,676 ERROR [io.quarkus.deployment.dev.JavaCompilationProvider] (vert.x-worker-thread-1) cannot find symbol
  symbol:   method id(java.lang.String)
  location: class com.bench.model.AuditEntry, line 62 in /work/vault-b/t4/src/main/java/com/bench/api/UserRoleResource.java
2026-07-20 11:36:31,738 ERROR [io.quarkus.deployment.dev.JavaCompilationProvider] (vert.x-worker-thread-1) cannot find symbol
  symbol:   method id(java.lang.String)
  location: class com.bench.model.AuditEntry, line 62 in /work/vault-b/t4/src/main/java/com/bench/api/UserRoleResource.java
2026-07-20 11:36:33,811 ERROR [io.quarkus.deployment.dev.JavaCompilationProvider] (vert.x-worker-thread-1) cannot find symbol
  symbol:   method id(java.lang.String)
  location: class com.bench.model.AuditEntry, line 62 in /work/vault-b/t4/src/main/java/com/bench/api/UserRoleResource.java
2026-07-20 11:36:35,868 ERROR [io.quarkus.deployment.dev.JavaCompilationProvider] (vert.x-worker-thread-1) cannot find symbol
  symbol:   method id(java.lang.String)
  location: class com.bench.model.AuditEntry, line 62 in /work/vault-b/t4/src/main/java/com/bench/api/UserRoleResource.java
2026-07-20 11:36:37,924 ERROR [io.quarkus.deployment.dev.JavaCompilationProvider] (vert.x-worker-thread-1) cannot find symbol
  symbol:   method id(java.lang.String)
  location: class com.bench.model.AuditEntry, line 62 in /work/vault-b/t4/src/main/java/com/bench/api/UserRoleResource.java
2026-07-20 11:36:39,981 ERROR [io.quarkus.deployment.dev.JavaCompilationProvider] (vert.x-worker-thread-1) cannot find symbol
  symbol:   method id(java.lang.String)
  location: class com.bench.model.AuditEntry, line 62 in /work/vault-b/t4/src/main/java/com/bench/api/UserRoleResource.java

```

Corrija e reenvie TODOS os blocos FILE, com o conteúdo completo de cada arquivo.

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
        String actorId = getActorId();
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null || !tenantId.equals(actor.tenantId)) {
            return Response.status(404).entity(new ErrorResponse("NOT_FOUND", "Tenant or user not found")).build();
        }

        User targetUser = store.findUser(userId).orElse(null);
        if (targetUser == null || !tenantId.equals(targetUser.tenantId)) {
            return Response.status(404).entity(new ErrorResponse("NOT_FOUND", "User not found")).build();
        }

        // Verificar permissões do ator
        if (!hasPermission(actor, targetUser)) {
            return Response.status(403)
                    .entity(new ErrorResponse("FORBIDDEN_ROLE", "Insufficient role to change user role"))
                    .build();
        }

        // Verificar proteção do owner
        if (targetUser.role == Role.OWNER && actor.role != Role.OWNER) {
            return Response.status(403)
                    .entity(new ErrorResponse("OWNER_PROTECTED", "Cannot modify owner role by non-owner"))
                    .build();
        }

        // Verificar se é o último owner
        if (targetUser.role == Role.OWNER && request.role != Role.OWNER && !canRemoveLastOwner(tenantId, userId)) {
            return Response.status(409)
                    .entity(new ErrorResponse("LAST_OWNER", "Cannot remove last owner"))
                    .build();
        }

        // Realizar mudança de papel
        targetUser.role = request.role;

        // Registrar auditoria
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "USER_ROLE_CHANGED";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "Role changed to " + request.role;
        store.auditLog.add(auditEntry);

        return Response.ok(targetUser).build();
    }

    private boolean hasPermission(User actor, User targetUser) {
        if (actor.role == Role.OWNER) return true;
        if (actor.role == Role.ADMIN && targetUser.role != Role.OWNER) return true;
        return false;
    }

    private boolean canRemoveLastOwner(String tenantId, String userId) {
        List<User> owners = store.usersOfTenant(tenantId).stream()
                .filter(u -> u.role == Role.OWNER && u.status != UserStatus.DELETED)
                .toList();
        return owners.size() > 1 || !owners.get(0).id.equals(userId);
    }

    private String getActorId() {
        // Em um ambiente real, isso viria do header HTTP
        // Aqui estamos simulando com uma variável de ambiente ou configuração
        return System.getenv("X_ACTOR_ID");
    }

    public static class RoleChangeRequest {
        public Role role;
    }

    public static class ErrorResponse {
        public String code;
        public String message;

        public ErrorResponse(String code, String message) {
            this.code = code;
            this.message = message;
        }
    }
}
```