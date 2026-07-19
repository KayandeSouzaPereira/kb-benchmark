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

ACTION: ls .

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

ACTION: grep papel

---

## user

RESULT (6 ações restantes):
202601051030-papeis-do-tenant.md:5: Mutações administrativas — convidar alguém, excluir usuário, mudar papel —
202601201300-auditoria-de-mutacoes.md:3: Toda mutação EFETIVADA de usuário/convite/papel grava um AuditEntry no
202601201330-codigos-de-erro-da-api.md:12: - 403 `FORBIDDEN_ROLE` — papel insuficiente ([[202601051030-papeis-do-tenant]])
202602101415-protecao-do-owner.md:6: Regra que fechamos: **ADMIN nunca altera nem exclui um OWNER** — nem papel,

---

## assistant

ACTION: read 202601051030-papeis-do-tenant.md

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

ACTION: read 202601201300-auditoria-de-mutacoes.md

---

## user

RESULT (2 ações restantes):
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


---

## assistant

ACTION: read 202601201330-codigos-de-erro-da-api.md

---

## user

RESULT (1 ações restantes):
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

FILE: src/main/java/com/bench/api/RoleChangeResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;

import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}/role")
public class RoleChangeResource {

    @Inject
    InMemoryStore store;

    @PATCH
    public Response changeRole(@PathParam("tenantId") String tenantId,
                              @PathParam("userId") String userId,
                              @HeaderParam("X-Actor-Id") String actorId,
                              @BeanParam RoleChangeRequest request) {
        // Verificar se o usuário existe
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User user = userOpt.get();
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Verificar se o ator existe
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User actor = actorOpt.get();
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Verificar permissões
        if (!hasPermission(actor, tenantId, user)) {
            if (user.role == Role.OWNER) {
                return Response.status(403).entity(new ErrorDTO("OWNER_PROTECTED")).build();
            } else {
                return Response.status(403).entity(new ErrorDTO("FORBIDDEN_ROLE")).build();
            }
        }

        // Verificar regra de último owner
        if (user.role == Role.OWNER && store.countOwners(tenantId) == 1) {
            return Response.status(409).entity(new ErrorDTO("LAST_OWNER")).build();
        }

        // Alterar papel
        user.role = request.role;
        store.auditLog.add(createAuditEntry(actorId, tenantId, user.id, "USER_ROLE_CHANGED"));

        return Response.ok(user).build();
    }

    private boolean hasPermission(User actor, String tenantId, User target) {
        // Verificar se o ator é do mesmo tenant
        if (!actor.tenantId.equals(tenantId)) {
            return false;
        }

        // Verificar permissões de papel
        if (actor.role == Role.OWNER) {
            return true;
        }

        if (actor.role == Role.ADMIN) {
            // ADMIN pode alterar papel de qualquer usuário, exceto OWNER
            return target.role != Role.OWNER;
        }

        // MEMBER não pode alterar papel
        return false;
    }

    private AuditEntry createAuditEntry(String actorId, String tenantId, String targetId, String action) {
        return new AuditEntry() {
            {
                this.id = UUID.randomUUID().toString();
                this.tenantId = tenantId;
                this.actorId = actorId;
                this.action = action;
                this.targetId = targetId;
                this.timestamp = Instant.now();
                this.details = "Role changed to " + request.role;
            }
        };
    }
}

class RoleChangeRequest {
    public Role role;
}
```

---

## user

A compilação/verificação do seu código falhou:

```
------------
[ERROR] COMPILATION ERROR : 
[INFO] -------------------------------------------------------------
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[48,56] cannot find symbol
  symbol:   class ErrorDTO
  location: class com.bench.api.RoleChangeResource
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[50,56] cannot find symbol
  symbol:   class ErrorDTO
  location: class com.bench.api.RoleChangeResource
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[56,52] cannot find symbol
  symbol:   class ErrorDTO
  location: class com.bench.api.RoleChangeResource
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[95,53] cannot find symbol
  symbol: variable request
[INFO] 4 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.488 s
[INFO] Finished at: 2026-07-19T16:26:31Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[48,56] cannot find symbol
[ERROR]   symbol:   class ErrorDTO
[ERROR]   location: class com.bench.api.RoleChangeResource
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[50,56] cannot find symbol
[ERROR]   symbol:   class ErrorDTO
[ERROR]   location: class com.bench.api.RoleChangeResource
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[56,52] cannot find symbol
[ERROR]   symbol:   class ErrorDTO
[ERROR]   location: class com.bench.api.RoleChangeResource
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[95,53] cannot find symbol
[ERROR]   symbol: variable request
[ERROR] -> [Help 1]
[ERROR] 
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR] 
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoFailureException

```

Corrija e reenvie TODOS os blocos FILE, com o conteúdo completo de cada arquivo.

---

## assistant

FILE: src/main/java/com/bench/api/RoleChangeResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;

import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}/role")
public class RoleChangeResource {

    @Inject
    InMemoryStore store;

    @PATCH
    public Response changeRole(@PathParam("tenantId") String tenantId,
                              @PathParam("userId") String userId,
                              @HeaderParam("X-Actor-Id") String actorId,
                              @BeanParam RoleChangeRequest request) {
        // Verificar se o usuário existe
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User user = userOpt.get();
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Verificar se o ator existe
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User actor = actorOpt.get();
        if (!actor.tenant,equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Verificar permissões
        if (!hasPermission(actor, tenantId, user)) {
            if (user.role == Role.OWNER) {
                return Response.status(403).entity(new ErrorDTO("OWNER_PROTECTED")).build();
            } else {
                return Response.status(403).entity(new ErrorDTO("FORBIDDEN_ROLE")).build();
            }
        }

        // Verificar regra de último owner
        if (user.role == Role.OWNER && store.countOwners(tenantId) == 1) {
            return Response.status(409).entity(new ErrorDTO("LAST_OWNER")).build();
        }

        // Alterar papel
        user.role = request.role;
        store.auditLog.add(createAuditEntry(actorId, tenantId, user.id, "USER_ROLE_CHANGED"));

        return Response.ok(user).build();
    }

    private boolean hasPermission(User actor, String tenantId, User target) {
        // Verificar se o ator é do mesmo tenant
        if (!actor.tenantId.equals(tenantId)) {
            return false;
        }

        // Verificar permissões de papel
        if (actor.role == Role.OWNER) {
            return true;
        }

        if (actor.role == Role.ADMIN) {
            // ADMIN pode alterar papel de qualquer usuário, exceto OWNER
            return target.role != Role.OWNER;
        }

        // MEMBER não pode alterar papel
        return false;
    }

    private AuditEntry createAuditEntry(String actorId, String tenantId, String targetId, String action) {
        return new AuditEntry() {
            {
                this.id = UUID.randomUUID().toString();
                this.tenantId = tenantId;
                this.actorId = actorId;
                this.action = action;
                this.targetId = targetId;
                this.timestamp = Instant.now();
                this.details = "Role changed to " + request.role;
            }
        };
    }
}

class RoleChangeRequest {
    public Role role;
}

class ErrorDTO {
    public String code;
    public String message;

    public ErrorDTO(String code) {
        this.code = code;
        this.message = "Error: " + code;
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
sem relatorio surefire (compilacao?)
[INFO] Scanning for projects...
[INFO] 
[INFO] ------------------------< com.bench:saas-users >------------------------
[INFO] Building saas-users 1.0.0
[INFO]   from pom.xml
[INFO] --------------------------------[ jar ]---------------------------------
[INFO] 
[INFO] --- resources:3.4.0:resources (default-resources) @ saas-users ---
[INFO] Copying 1 resource from src/main/resources to target/classes
[INFO] 
[INFO] --- compiler:3.15.0:compile (default-compile) @ saas-users ---
[INFO] Recompiling the module because of changed source code.
[INFO] Compiling 10 source files with javac [debug release 21] to target/classes
[INFO] -------------------------------------------------------------
[ERROR] COMPILATION ERROR : 
[INFO] -------------------------------------------------------------
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[41,26] ')' expected
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[41,43] ';' expected
[INFO] 2 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.191 s
[INFO] Finished at: 2026-07-19T16:27:27Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[41,26] ')' expected
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[41,43] ';' expected
[ERROR] -> [Help 1]
[ERROR] 
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR] 
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoFailureException

```

Corrija e reenvie TODOS os blocos FILE, com o conteúdo completo de cada arquivo.

---

## assistant

FILE: src/main/java/com/bench/api/RoleChangeResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;

import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}/role")
public class RoleChangeResource {

    @Inject
    InMemoryStore store;

    @PATCH
    public Response changeRole(@PathParam("tenantId") String tenantId,
                              @PathParam("userId") String userId,
                              @HeaderParam("X-Actor-Id") String actorId,
                              @BeanParam RoleChangeRequest request) {
        // Verificar se o usuário existe
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User user = userOpt.get();
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Verificar se o ator existe
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User actor = actorOpt.get();
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Verificar permissões
        if (!hasPermission(actor, tenantId, user)) {
            if (user.role == Role.OWNER) {
                return Response.status(403).entity(new ErrorDTO("OWNER_PROTECTED")).build();
            } else {
                return Response.status(403).entity(new ErrorDTO("FORBIDDEN_ROLE")).build();
            }
        }

        // Verificar regra de último owner
        if (user.role == Role.OWNER && store.countOwners(tenantId) == 1) {
            return Response.status(409).entity(new ErrorDTO("LAST_OWNER")).build();
        }

        // Alterar papel
        user.role = request.role;
        store.auditLog.add(createAuditEntry(actorId, tenantId, user.id, "USER_ROLE_CHANGED"));

        return Response.ok(user).build();
    }

    private boolean hasPermission(User actor, String tenantId, User target) {
        // Verificar se o ator é do mesmo tenant
        if (!actor.tenantId.equals(tenantId)) {
            return false;
        }

        // Verificar permissões de papel
        if (actor.role == Role.OWNER) {
            return true;
        }

        if (actor.role == Role.ADMIN) {
            // ADMIN pode alterar papel de qualquer usuário, exceto OWNER
            return target.role != Role.OWNER;
        }

        // MEMBER não pode alterar papel
        return false;
    }

    private AuditEntry createAuditEntry(String actorId, String tenantId, String targetId, String action) {
        return new AuditEntry() {
            {
                this.id = UUID.randomUUID().toString();
                this.tenantId = tenantId;
                this.actorId = actorId;
                this.action = action;
                this.targetId = targetId;
                this.timestamp = Instant.now();
                this.details = "Role changed to " + request.role;
            }
        };
    }
}

class RoleChangeRequest {
    public Role role;
}

class ErrorDTO {
    public String code;
    public String message;

    public ErrorDTO(String code) {
        this.code = code;
        this.message = "Error: " + code;
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
sem relatorio surefire (compilacao?)
[INFO] Scanning for projects...
[INFO] 
[INFO] ------------------------< com.bench:saas-users >------------------------
[INFO] Building saas-users 1.0.0
[INFO]   from pom.xml
[INFO] --------------------------------[ jar ]---------------------------------
[INFO] 
[INFO] --- resources:3.4.0:resources (default-resources) @ saas-users ---
[INFO] Copying 1 resource from src/main/resources to target/classes
[INFO] 
[INFO] --- compiler:3.15.0:compile (default-compile) @ saas-users ---
[INFO] Recompiling the module because of changed source code.
[INFO] Compiling 10 source files with javac [debug release 21] to target/classes
[INFO] -------------------------------------------------------------
[ERROR] COMPILATION ERROR : 
[INFO] -------------------------------------------------------------
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[95,53] cannot find symbol
  symbol: variable request
[INFO] 1 error
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.588 s
[INFO] Finished at: 2026-07-19T16:28:29Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure
[ERROR] /work/vault-b/t4/src/main/java/com/bench/api/RoleChangeResource.java:[95,53] cannot find symbol
[ERROR]   symbol: variable request
[ERROR] -> [Help 1]
[ERROR] 
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR] 
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoFailureException

```

Corrija e reenvie TODOS os blocos FILE, com o conteúdo completo de cada arquivo.

---

## assistant

FILE: src/main/java/com/bench/api/RoleChangeResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;

import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/users/{userId}/role")
public class RoleChangeResource {

    @Inject
    InMemoryStore store;

    @PATCH
    public Response changeRole(@PathParam("tenantId") String tenantId,
                              @PathParam("userId") String userId,
                              @HeaderParam("X-Actor-Id") String actorId,
                              @BeanParam RoleChangeRequest request) {
        // Verificar se o usuário existe
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User user = userOpt.get();
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Verificar se o ator existe
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User actor = actorOpt.get();
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Verificar permissões
        if (!hasPermission(actor, tenantId, user)) {
            if (user.role == Role.OWNER) {
                return Response.status(403).entity(new ErrorDTO("OWNER_PROTECTED")).build();
            } else {
                return Response.status(403).entity(new ErrorDTO("FORBIDDEN_ROLE")).build();
            }
        }

        // Verificar regra de último owner
        if (user.role == Role.OWNER && store.countOwners(tenantId) == 1) {
            return Response.status(409).entity(new ErrorDTO("LAST_OWNER")).build();
        }

        // Alterar papel
        user.role = request.role;
        store.auditLog.add(createAuditEntry(actorId, tenantId, user.id, "USER_ROLE_CHANGED"));

        return Response.ok(user).build();
    }

    private boolean hasPermission(User actor, String tenantId, User target) {
        // Verificar se o ator é do mesmo tenant
        if (!actor.tenantId.equals(tenantId)) {
            return false;
        }

        // Verificar permissões de papel
        if (actor.role == Role.OWNER) {
            return true;
        }

        if (actor.role == Role.ADMIN) {
            // ADMIN pode alterar papel de qualquer usuário, exceto OWNER
            return target.role != Role.OWNER;
        }

        // MEMBER não pode alterar papel
        return false;
    }

    private AuditEntry createAuditEntry(String actorId, String tenantId, String targetId, String action) {
        return new AuditEntry() {
            {
                this.id = UUID.randomUUID().toString();
                this.tenantId = tenantId;
                this.actorId = actorId;
                this.action = action;
                this.targetId = targetId;
                this.timestamp = Instant.now();
                this.details = "Role changed to " + request.role;
            }
        };
    }
}

class RoleChangeRequest {
    public Role role;
}

class ErrorDTO {
    public String code;
    public String message;

    public ErrorDTO(String code) {
        this.code = code;
        this.message = "Error: " + code;
    }
}
```