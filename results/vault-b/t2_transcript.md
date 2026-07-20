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

ACTION: ls .
FILE: caminho/relativo/do/Arquivo.java
```java
com.bench.api
com.bench.model
com.bench.store
```
FILE: com.bench/api/DeleteUserResource.java
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
public class DeleteUserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(@PathParam("tenantId") String tenantId, @PathParam("userId") String userId) {
        // 1. Validação de parâmetros
        if (tenantId == null || tenantId.isEmpty() || userId == null || userId.isEmpty()) {
            return Response.status(422).entity("Tenant ID e User ID são obrigatórios").build();
        }

        // 2. Verifica se o usuário autenticado existe
        String actorId = javax.ws.rs.core.Context.getHeaderString("X-Actor-Id");
        if (actorId == null || actorId.isEmpty()) {
            return Response.status(401).entity("Autenticação necessária").build();
        }

        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(401).entity("Usuário autenticado não encontrado").build();
        }
        User actor = actorOpt.get();

        // 3. Verifica se o tenant existe
        if (!store.tenants.containsKey(tenantId)) {
            return Response.status(404).entity("Tenant não encontrado").build();
        }

        // 4. Verifica se o usuário a ser excluído existe
        Optional<User> userOpt = store.findUser(userId);
        if (!userOpt.isPresent()) {
            return Response.status(404).entity("Usuário não encontrado").build();
        }
        User user = userOpt.get();

        // 5. Verifica se o usuário pertence ao tenant
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(403).entity("Acesso negado: usuário não pertence ao tenant").build();
        }

        // 6. Verifica se o ator tem permissão para excluir (OWNER ou ADMIN)
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return Response.status(403).entity("Acesso negado: apenas OWNERs e ADMINs podem excluir usuários").build();
        }

        // 7. Verifica se o usuário a ser excluído é o próprio ator
        if (actor.id.equals(userId)) {
            return Response.status(422).entity("Não é possível excluir o próprio usuário").build();
        }

        // 8. Verifica se o usuário é o único OWNER do tenant
        if (user.role == Role.OWNER && store.countOwners(tenantId) <= 1) {
            return Response.status(422).entity("Não é possível excluir o único OWNER do tenant").build();
        }

        // 9. Exclusão real do usuário
        user.status = UserStatus.DELETED;
        user.deletedAt = Instant.now();

        // 10. Calcula data de purga (30 dias após exclusão)
        user.purgeAt = user.deletedAt.plus(java.time.Duration.ofDays(30));

        // 11. Registra auditoria
        AuditEntry audit = new AuditEntry();
        audit.id = java.util.UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "DELETE_USER";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "Usuário excluído. Motivo: Exclusão via API.";

        store.auditLog.add(audit);

        return Response.noContent().build();
    }
}
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

(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

ACTION: read 202601050900-mapa-dominio-usuarios.md
ACTION: read 202601201300-auditoria-de-mutacoes.md
ACTION: read 202601201330-codigos-de-erro-da-api.md
ACTION: read 202602101415-protecao-do-owner.md
ACTION: read 202602101430-ultimo-owner.md
ACTION: read 202603150900-soft-delete-30-dias.md
ACTION: read 202603150930-quem-pode-deletar.md
ACTION: read 202604010900-mapa-api-e-convencoes.md

---

## user

RESULT (6 ações restantes):
# 202601050900 Mapa — domínio de gestão de usuários

Nota-índice do que já pensei sobre o domínio de usuários do produto.

- Papéis e hierarquia: [[202601051030-papeis-do-tenant]]
- Proteções especiais do owner: [[202602101415-protecao-do-owner]] e [[202602101430-ultimo-owner]]
- Isolamento entre tenants: [[202602151100-isolamento-de-tenant-404]]
- Limites de assentos: [[202601121000-limites-por-plano]] (atenção à correção em [[202605021430-convites-pendentes-contam]])
- Convites: [[202602041100-expiracao-de-convites-72h]], [[202602041130-reenvio-de-convites]]
- Exclusão: [[202603150900-soft-delete-30-dias]], [[202603150930-quem-pode-deletar]]
- Auditoria: [[202601201300-auditoria-de-mutacoes]]
- Autenticação (separado do domínio de gestão): [[202601080800-lockout-e-senhas]]

Convenções de código ficam em outro mapa: [[202604010900-mapa-api-e-convencoes]].


---

## assistant

ACTION: read 202603150900-soft-delete-30-dias.md
ACTION: read 202603150930-quem-pode-deletar.md
ACTION: read 202602101415-protecao-do-owner.md
ACTION: read 202602101430-ultimo-owner.md
ACTION: read 202601201330-codigos-de-erro-da-api.md
ACTION: read 202604010900-mapa-api-e-convencoes.md

---

## user

RESULT (5 ações restantes):
# 202603150900 Soft-delete com purge em 30 dias

Não existe hard delete de usuário no produto. Excluir =

- `status = DELETED`
- `deletedAt = agora`
- `purgeAt = agora + 30 dias` (o job de purge definitivo lê esse campo)
- o registro CONTINUA no store

Sucesso responde 204 No Content. Restaurar dentro da janela é permitido
(ação de auditoria `USER_RESTORED`).

30 dias foi acordo com jurídico: compliance pede trilha mínima de 30,
LGPD derrubou a ideia de 90. Cogitei flag booleana `deleted` e descartei —
sem `purgeAt` o job de purge não funciona.

Quem pode excluir: [[202603150930-quem-pode-deletar]].
Auditoria da exclusão: [[202601201300-auditoria-de-mutacoes]].


---

## assistant

ACTION: read 202603150930-quem-pode-deletar.md
ACTION: read 202601201300-auditoria-de-mutacoes.md
ACTION: read 202602151100-isolamento-de-tenant-404.md

---

## user

RESULT (4 ações restantes):
# 202603150930 Quem pode excluir usuário

- ADMIN+ do próprio tenant ([[202601051030-papeis-do-tenant]],
  [[202602151100-isolamento-de-tenant-404]]).
- ADMIN não exclui OWNER → 403 `OWNER_PROTECTED`
  ([[202602101415-protecao-do-owner]]).
- **Ninguém exclui a si mesmo** → 422 `CANNOT_DELETE_SELF`. Dois motivos:
  evita tenant órfão por engano e limita estrago de sessão roubada.
- A exclusão em si é sempre soft ([[202603150900-soft-delete-30-dias]]) e
  audita `USER_SOFT_DELETED` com targetId = usuário excluído
  ([[202601201300-auditoria-de-mutacoes]]).


---

## assistant

ACTION: read 202601201300-auditoria-de-mutacoes.md
ACTION: read 202602101415-protecao-do-owner.md
ACTION: read 202601201330-codigos-de-erro-da-api.md
FILE: com/bench/api/DeleteUserResource.java
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
public class DeleteUserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(@PathParam("tenantId") String tenantId, @PathParam("userId") String userId) {
        // 1. Validação de parâmetros
        if (tenantId == null || tenantId.isEmpty() || userId == null || userId.isEmpty()) {
            return Response.status(422).entity("Tenant ID e User ID são obrigatórios").build();
        }

        // 2. Verifica se o usuário autenticado existe
        String actorId = javax.ws.rs.core.Context.getHeaderString("X-Actor-Id");
        if (actorId == null || actorId.isEmpty()) {
            return Response.status(401).entity("Autenticação necessária").build();
        }

        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(401).entity("Usuário autenticado não encontrado").build();
        }
        User actor = actorOpt.get();

        // 3. Verifica se o tenant existe
        if (!store.tenants.containsKey(tenantId)) {
            return Response.status(404).entity("Tenant não encontrado").build();
        }

        // 4. Verifica se o usuário a ser excluído existe
        Optional<User> userOpt = store.findUser(userId);
        if (!userOpt.isPresent()) {
            return Response.status(404).entity("Usuário não encontrado").build();
        }
        User user = userOpt.get();

        // 5. Verifica se o usuário pertence ao tenant
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(403).entity("Acesso negado: usuário não pertence ao tenant").build();
        }

        // 6. Verifica se o ator tem permissão para excluir (OWNER ou ADMIN)
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return Response.status(403).entity("Acesso negado: apenas OWNERs e ADMINs podem excluir usuários").build();
        }

        // 7. Verifica se o usuário a ser excluído é o próprio ator
        if (actor.id.equals(userId)) {
            return Response.status(422).entity("Não é possível excluir o próprio usuário").build();
        }

        // 8. Verifica se o usuário é o único OWNER do tenant
        if (user.role == Role.OWNER && store.countOwners(tenantId) <= 1) {
            return Response.status(422).entity("Não é possível excluir o único OWNER do tenant").build();
        }

        // 9. Verifica se o usuário a ser excluído é um OWNER e o ator não é OWNER
        if (user.role == Role.OWNER && actor.role != Role.OWNER) {
            return Response.status(403).entity("Acesso negado: apenas OWNERs podem excluir outros OWNERs").build();
        }

        // 10. Exclusão real do usuário
        user.status = UserStatus.DELETED;
        user.deletedAt = Instant.now();

        // 11. Calcula data de purga (30 dias após exclusão)
        user.purgeAt = user.deletedAt.plus(java.time.Duration.ofDays(30));

        // 12. Registra auditoria
        AuditEntry audit = new AuditEntry();
        audit.id = java.util.UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_SOFT_DELETED";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "Usuário excluído. Motivo: Exclusão via API.";

        store.auditLog.add(audit);

        return Response.noContent().build();
    }
}
```

---

## user

RESULT (3 ações restantes):
# 202601201300 Auditoria de mutações

Toda mutação EFETIVADA de usuário/convite/papel grava um AuditEntry no
auditLog, na mesma operação (nada de "audito depois"). Tentativa negada
(403/422) NÃO gera entrada.

Campos: `id` (UUID novo), `tenantId`, `actorId` (o `X-Actor-Id`), `action`,
`targetId` (id do recurso afetado), `timestamp` (Instant UTC), `details`
(livre, opcional).

Ações válidas — não inventar strings fora desta lista, dashboards de
compliance quebram:

- `USER_INVITED` (targetId = id do convite)
- `INVITATION_RESENT` (targetId = id do convite)
- `USER_ROLE_CHANGED` (targetId = id do usuário)
- `USER_SOFT_DELETED` (targetId = id do usuário)
- `USER_RESTORED` (targetId = id do usuário)

Liga com tudo: [[202602041100-expiracao-de-convites-72h]],
[[202603150900-soft-delete-30-dias]], [[202601051030-papeis-do-tenant]].


(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

ACTION: read 202601051030-papeis-do-tenant.md
ACTION: read 202602101430-ultimo-owner.md
ACTION: read 202605021430-convites-pendentes-contam.md

---

## user

RESULT (2 ações restantes):
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

FILE: com/bench/api/DeleteUserResource.java
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
public class DeleteUserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(@PathParam("tenantId") String tenantId, @PathParam("userId") String userId) {
        // 1. Validação de parâmetros
        if (tenantId == null || tenantId.isEmpty() || userId == null || userId.isEmpty()) {
            return Response.status(422).entity("Tenant ID e User ID são obrigatórios").build();
        }

        // 2. Verifica se o usuário autenticado existe
        String actorId = javax.ws.rs.core.Context.getHeaderString("X-Actor-Id");
        if (actorId == null || actorId.isEmpty()) {
            return Response.status(401).entity("Autenticação necessária").build();
        }

        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(401).entity("Usuário autenticado não encontrado").build();
        }
        User actor = actorOpt.get();

        // 3. Verifica se o tenant existe
        if (!store.tenants.containsKey(tenantId)) {
            return Response.status(404).entity("Tenant não encontrado").build();
        }

        // 4. Verifica se o usuário a ser excluído existe
        Optional<User> userOpt = store.findUser(userId);
        if (!userOpt.isPresent()) {
            return Response.status(404).entity("Usuário não encontrado").build();
        }
        User user = userOpt.get();

        // 5. Verifica se o usuário pertence ao tenant
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(403).entity("Acesso negado: usuário não pertence ao tenant").build();
        }

        // 6. Verifica se o ator tem permissão para excluir (OWNER ou ADMIN)
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return Response.status(403).entity("Acesso negado: apenas OWNERs e ADMINs podem excluir usuários").build();
        }

        // 7. Verifica se o usuário a ser excluído é o próprio ator
        if (actor.id.equals(userId)) {
            return Response.status(422).entity("Não é possível excluir o próprio usuário").build();
        }

        // 8. Verifica se o usuário é o único OWNER do tenant
        if (user.role == Role.OWNER && store.countOwners(tenantId) <= 1) {
            return Response.status(422).entity("Não é possível excluir o único OWNER do tenant").build();
        }

        // 9. Verifica se o usuário a ser excluído é um OWNER e o ator não é OWNER
        if (user.role == Role.OWNER && actor.role != Role.OWNER) {
            return Response.status(403).entity("Acesso negado: apenas OWNERs podem excluir outros OWNERs").build();
        }

        // 10. Exclusão real do usuário
        user.status = UserStatus.DELETED;
        user.deletedAt = Instant.now();

        // 11. Calcula data de purga (30 dias após exclusão)
        user.purgeAt = user.deletedAt.plus(java.time.Duration.ofDays(30));

        // 12. Registra auditoria
        AuditEntry audit = new AuditEntry();
        audit.id = java.util.UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_SOFT_DELETED";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "Usuário excluído. Motivo: Exclusão via API.";

        store.auditLog.add(audit);

        return Response.noContent().build();
    }
}
```