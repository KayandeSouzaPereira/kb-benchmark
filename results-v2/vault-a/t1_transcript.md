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

# Tarefa: criar convite de usuário

Implemente o endpoint de criação de convite:

```
POST /tenants/{tenantId}/invitations
Request JSON:  { "email": "pessoa@ex.com", "role": "ADMIN" | "MEMBER" }
Sucesso: 201 com JSON { "id": "...", "expiresAt": "..." }
```

Persista o convite no `InMemoryStore`. Implemente TODAS as regras de negócio,
permissões, validações e convenções de erro/auditoria que o time definiu para
convites.


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

ACTION: ls .

---

## user

RESULT (7 ações restantes):
INDEX.md
decisoes/
dominio/
padroes-codigo/
produto/
runbooks/

---

## assistant

ACTION: ls decisoes/

---

## user

RESULT (6 ações restantes):
adr-001-soft-delete-com-retencao.md
adr-002-convites-pendentes-contam-no-limite.md

---

## assistant

ACTION: read decisoes/adr-002-convites-pendentes-contam-no-limite.md

---

## user

RESULT (5 ações restantes):
---
tipo: adr
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# ADR-002 — Convites pendentes contam no limite de assentos do plano

## Decisão

`assentos ocupados = usuários não-DELETED + convites PENDING`. Vale para toda
verificação de limite de plano.

## Contexto

Sem isso, um tenant FREE convidava 30 pessoas e todas conseguiam aceitar,
estourando o plano. Billing e produto decidiram em 2026-05-02 que a vaga é
reservada no momento do convite.

## Alternativas descartadas — não propor novamente

- **Contar só usuários ativos**: permite estourar o plano via convites em massa
  (bug real do incidente #482).
- **Bloquear na aceitação**: péssima UX — a pessoa clica no e-mail e descobre
  que não há vaga.

## Relacionados

- [../dominio/limites-de-plano.md](../dominio/limites-de-plano.md)
- [../dominio/convites.md](../dominio/convites.md)


---

## assistant

ACTION: ls dominio/

---

## user

RESULT (4 ações restantes):
auditoria.md
autenticacao-e-lockout.md
convites.md
exclusao-de-usuarios.md
limites-de-plano.md
papeis-e-permissoes.md

---

## assistant

ACTION: read dominio/limites-de-plano.md

---

## user

RESULT (3 ações restantes):
---
tipo: regra-de-negocio
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# Limites de usuários por plano

| Plano | Máximo de assentos |
|---|---|
| FREE | 5 |
| PRO | 50 |
| ENTERPRISE | ilimitado (`maxUsers = null`) |

## O que conta como assento ocupado

`assentos ocupados = usuários do tenant com status != DELETED + convites com status PENDING`

Ou seja: **convite pendente ocupa vaga** (decisão registrada em
[adr-002](../decisoes/adr-002-convites-pendentes-contam-no-limite.md)).
Usuários INVITED, ACTIVE e SUSPENDED contam; DELETED não conta.

## Regra de bloqueio

Criar um convite quando `assentos ocupados >= máximo do plano` retorna
`422 PLAN_LIMIT_EXCEEDED` e **não** persiste nada.

## Quando usar / Quando NÃO usar

- Use ao criar convites e ao reativar usuários.
- NÃO aplique o limite ao reenviar um convite já existente (não cria assento novo).

## Relacionados

- [convites](convites.md)
- [../decisoes/adr-002-convites-pendentes-contam-no-limite.md](../decisoes/adr-002-convites-pendentes-contam-no-limite.md)
- [../produto/planos-e-precos.md](../produto/planos-e-precos.md)


---

## assistant

ACTION: read dominio/convites.md

---

## user

RESULT (2 ações restantes):
---
tipo: regra-de-negocio
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# Ciclo de vida do convite

## Criação

- Somente ADMIN+ cria convites (ver [papeis-e-permissoes](papeis-e-permissoes.md)).
- Respeita o limite do plano — convite pendente conta como assento
  (ver [limites-de-plano](limites-de-plano.md)).
- **Todo convite expira em 72 horas** a partir da criação: `expiresAt = createdAt + 72h`.
- Convite nasce com `status = PENDING` e `resendCount = 0`.
- Auditoria obrigatória: ação `USER_INVITED` (ver [auditoria](auditoria.md)).

## Reenvio

- Somente ADMIN+.
- **Máximo de 3 reenvios por convite.** O 4º retorna `422 RESEND_LIMIT_REACHED`
  e não altera nada.
- Cada reenvio **reseta a expiração para +72h a partir de agora** e incrementa
  `resendCount`.
- Reenviar um convite já expirado é permitido e o **reativa** (nova janela de 72h).
- Auditoria obrigatória: ação `INVITATION_RESENT`.

## Aceitação

- Aceitar convite expirado retorna `410 INVITATION_EXPIRED`.
- Aceitação cria o usuário com `status = ACTIVE` e marca o convite como `ACCEPTED`.

## Anti-padrões já observados

- Aplicar o limite de plano no reenvio (errado: reenvio não cria assento).
- Esquecer de resetar `expiresAt` no reenvio.

## Relacionados

- [papeis-e-permissoes](papeis-e-permissoes.md)
- [limites-de-plano](limites-de-plano.md)
- [auditoria](auditoria.md)
- [../padroes-codigo/formato-de-erros-api.md](../padroes-codigo/formato-de-erros-api.md)


---

## assistant

ACTION: read dominio/papeis-e-permissoes.md

---

## user

RESULT (1 ações restantes):
---
tipo: regra-de-negocio
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# Papéis e permissões

Hierarquia dentro de um tenant: `OWNER > ADMIN > MEMBER`.

## Regras

- **Convidar usuários, excluir usuários e alterar papéis exige ADMIN ou OWNER** (ADMIN+).
  MEMBER que tentar recebe `403 FORBIDDEN_ROLE`.
- **ADMIN nunca altera nem exclui um OWNER** (nem papel, nem exclusão): `403 OWNER_PROTECTED`.
  Somente um OWNER pode mexer em outro OWNER ou promover alguém a OWNER.
- **O tenant nunca pode ficar sem OWNER**: rebaixar ou remover o último OWNER ativo
  retorna `409 LAST_OWNER`. Com dois ou mais owners, um owner pode rebaixar o outro.
- **Isolamento de tenant**: o ator (header `X-Actor-Id`) precisa pertencer ao tenant da URL.
  Ator de outro tenant recebe `404 NOT_FOUND` — nunca 403, para não vazar a existência
  do recurso.

## Quando usar / Quando NÃO usar

- Use em todo endpoint de mutação de usuários, convites ou papéis.
- NÃO confunda com autenticação (login/senha) — ver [autenticacao-e-lockout](autenticacao-e-lockout.md).

## Anti-padrões já observados

- Checar papel depois de mutar o estado (validar SEMPRE antes de escrever no store).
- Retornar 403 para ator de outro tenant (vaza existência; o correto é 404).

## Relacionados

- [exclusao-de-usuarios](exclusao-de-usuarios.md)
- [convites](convites.md)
- [../padroes-codigo/formato-de-erros-api.md](../padroes-codigo/formato-de-erros-api.md)
- [auditoria](auditoria.md)


---

## assistant

FILE: src/main/java/com/bench/api/InvitationResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;
import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/invitations")
public class InvitationResource {
    @Inject
    InMemoryStore store;

    @POST
    public Response createInvitation(
        @PathParam("tenantId") String tenantId,
        @HeaderParam("X-Actor-Id") String actorId,
        @BeanParam Request request
    ) {
        // Validate actor belongs to tenant
        User actor = store.findUser(actorId);
        if (actor == null || !actor.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Check if actor has permission to invite
        if (!hasPermission(actor, tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // Check plan limit
        Tenant tenant = store.findUser(tenantId).tenantId.equals(tenantId) ? 
            store.findUser(tenantId) : store.findUser(tenantId);
        if (tenant == null) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        long occupiedSeats = countOccupiedSeats(tenantId);
        if (occupiedSeats >= getMaxUsers(tenant)) {
            return Response.status(Response.Status.UNPROCESSABLE_ENTITY)
                .entity(Map.of("error", "PLAN_LIMIT_EXCEEDED"))
                .build();
        }

        // Create invitation
        Invitation invitation = new Invitation();
        invitation.id = UUID.randomUUID().toString();
        invitation.tenantId = tenantId;
        invitation.email = request.email;
        invitation.role = request.role;
        invitation.createdAt = Instant.now();
        invitation.expiresAt = invitation.createdAt.plusHours(72);
        invitation.resendCount = 0;
        invitation.status = InvitationStatus.PENDING;

        store.invitations.put(invitation.id, invitation);

        // Audit log
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_INVITED";
        audit.targetId = invitation.id;
        audit.timestamp = Instant.now();
        audit.details = String.format("Invitation created for %s", request.email);
        store.auditLog.add(audit);

        return Response.status(Response.Status.CREATED)
            .entity(Map.of(
                "id", invitation.id,
                "expiresAt", invitation.expiresAt.toString()
            ))
            .build();
    }

    private boolean hasPermission(User actor, String tenantId) {
        if (actor == null) return false;
        if (!actor.tenantId.equals(tenantId)) return false;

        // Check if actor is ADMIN or OWNER
        if (actor.role == Role.ADMIN || actor.role == Role.OWNER) {
            return true;
        }

        return false;
    }

    private long countOccupiedSeats(String tenantId) {
        long userCount = store.usersOfTenant(tenantId).stream()
            .filter(user -> user.status != UserStatus.DELETED)
            .count();

        long invitationCount = store.invitationsOfTenant(tenantId).stream()
            .filter(invitation -> invitation.status == InvitationStatus.PENDING)
            .count();

        return userCount + invitationCount;
    }

    private int getMaxUsers(Tenant tenant) {
        if (tenant.plan == Plan.ENTERPRISE) {
            return Integer.MAX_VALUE;
        }
        return tenant.plan == Plan.FREE ? 5 : 50;
    }
}

record Request(String email, Role role) {}
```

---

## user

A compilação/verificação do seu código falhou:

```

[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.637 s
[INFO] Finished at: 2026-07-19T15:14:52Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[23,36] incompatible types: java.util.Optional<com.bench.model.User> cannot be converted to com.bench.model.User
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[34,49] cannot find symbol
[ERROR]   symbol:   variable tenantId
[ERROR]   location: class java.util.Optional<com.bench.model.User>
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[35,27] incompatible types: bad type in conditional expression
[ERROR]     java.util.Optional<com.bench.model.User> cannot be converted to com.bench.model.Tenant
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[35,54] incompatible types: bad type in conditional expression
[ERROR]     java.util.Optional<com.bench.model.User> cannot be converted to com.bench.model.Tenant
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[42,51] cannot find symbol
[ERROR]   symbol:   variable UNPROCESSABLE_ENTITY
[ERROR]   location: class jakarta.ws.rs.core.Response.Status
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[51,35] email has private access in com.bench.api.Request
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[52,34] role has private access in com.bench.api.Request
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[54,52] cannot find symbol
[ERROR]   symbol:   method plusHours(int)
[ERROR]   location: variable createdAt of type java.time.Instant
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[68,75] email has private access in com.bench.api.Request
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

FILE: src/main/java/com/bench/api/InvitationResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;
import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/invitations")
public class InvitationResource {
    @Inject
    InMemoryStore store;

    @POST
    public Response createInvitation(
        @PathParam("tenantId") String tenantId,
        @HeaderParam("X-Actor-Id") String actorId,
        @BeanParam Request request
    ) {
        // Validate actor belongs to tenant
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null || !actor.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Check if actor has permission to invite
        if (!hasPermission(actor, tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // Find tenant
        Tenant tenant = store.findUser(tenantId).orElse(null);
        if (tenant == null) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Check plan limit
        long occupiedSeats = countOccupiedSeats(tenantId);
        if (occupiedSeats >= getMaxUsers(tenant)) {
            return Response.status(Response.Status.UNPROCESSABLE_ENTITY)
                .entity(Map.of("error", "PLAN_LIMIT_EXCEEDED"))
                .build();
        }

        // Create invitation
        Invitation invitation = new Invitation();
        invitation.id = UUID.randomUUID().toString();
        invitation.tenantId = tenantId;
        invitation.email = request.email();
        invitation.role = request.role();
        invitation.createdAt = Instant.now();
        invitation.expiresAt = invitation.createdAt.plusHours(72);
        invitation.resendCount = 0;
        invitation.status = InvitationStatus.PENDING;

        store.invitations.put(invitation.id, invitation);

        // Audit log
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_INVITED";
        audit.targetId = invitation.id;
        audit.timestamp = Instant.now();
        audit.details = String.format("Invitation created for %s", invitation.email);
        store.auditLog.add(audit);

        return Response.status(Response.Status.CREATED)
            .entity(Map.of(
                "id", invitation.id,
                "expiresAt", invitation.expiresAt.toString()
            ))
            .build();
    }

    private boolean hasPermission(User actor, String tenantId) {
        if (actor == null) return false;
        if (!actor.tenantId.equals(tenantId)) return false;

        // Check if actor is ADMIN or OWNER
        return actor.role == Role.ADMIN || actor.role == Role.OWNER;
    }

    private long countOccupiedSeats(String tenantId) {
        long userCount = store.usersOfTenant(tenantId).stream()
            .filter(user -> user.status != UserStatus.DELETED)
            .count();

        long invitationCount = store.invitationsOfTenant(tenantId).stream()
            .filter(invitation -> invitation.status == InvitationStatus.PENDING)
            .count();

        return userCount + invitationCount;
    }

    private int getMaxUsers(Tenant tenant) {
        if (tenant.plan == Plan.ENTERPRISE) {
            return Integer.MAX_VALUE;
        }
        return tenant.plan == Plan.FREE ? 5 : 50;
    }
}

record Request(String email, Role role) {}
```

---

## user

A compilação/verificação do seu código falhou:

```
5.0:compile (default-compile) @ saas-users ---
[INFO] Recompiling the module because of changed source code.
[INFO] Compiling 10 source files with javac [debug release 21] to target/classes
[INFO] -------------------------------------------------------------
[ERROR] COMPILATION ERROR : 
[INFO] -------------------------------------------------------------
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[34,56] incompatible types: com.bench.model.User cannot be converted to com.bench.model.Tenant
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[42,51] cannot find symbol
  symbol:   variable UNPROCESSABLE_ENTITY
  location: class jakarta.ws.rs.core.Response.Status
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[54,52] cannot find symbol
  symbol:   method plusHours(int)
  location: variable createdAt of type java.time.Instant
[INFO] 3 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.548 s
[INFO] Finished at: 2026-07-19T15:15:45Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[34,56] incompatible types: com.bench.model.User cannot be converted to com.bench.model.Tenant
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[42,51] cannot find symbol
[ERROR]   symbol:   variable UNPROCESSABLE_ENTITY
[ERROR]   location: class jakarta.ws.rs.core.Response.Status
[ERROR] /work/vault-a/t1/src/main/java/com/bench/api/InvitationResource.java:[54,52] cannot find symbol
[ERROR]   symbol:   method plusHours(int)
[ERROR]   location: variable createdAt of type java.time.Instant
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

FILE: src/main/java/com/bench/api/InvitationResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;
import java.time.Instant;
import java.util.*;

@Path("/tenants/{tenantId}/invitations")
public class InvitationResource {
    @Inject
    InMemoryStore store;

    @POST
    public Response createInvitation(
        @PathParam("tenantId") String tenantId,
        @HeaderParam("X-Actor-Id") String actorId,
        @BeanParam Request request
    ) {
        // Validate actor belongs to tenant
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null || !actor.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Check if actor has permission to invite
        if (!hasPermission(actor, tenantId)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // Find tenant
        Tenant tenant = store.findTenant(tenantId).orElse(null);
        if (tenant == null) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Check plan limit
        long occupiedSeats = countOccupiedSeats(tenantId);
        if (occupiedSeats >= getMaxUsers(tenant)) {
            return Response.status(Response.Status.UNPROCESSABLE_ENTITY)
                .entity(Map.of("error", "PLAN_LIMIT_EXCEEDED"))
                .build();
        }

        // Create invitation
        Invitation invitation = new Invitation();
        invitation.id = UUID.randomUUID().toString();
        invitation.tenantId = tenantId;
        invitation.email = request.email();
        invitation.role = request.role();
        invitation.createdAt = Instant.now();
        invitation.expiresAt = invitation.createdAt.plusHours(72);
        invitation.resendCount = 0;
        invitation.status = InvitationStatus.PENDING;

        store.invitations.put(invitation.id, invitation);

        // Audit log
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_INVITED";
        audit.targetId = invitation.id;
        audit.timestamp = Instant.now();
        audit.details = String.format("Invitation created for %s", invitation.email);
        store.auditLog.add(audit);

        return Response.status(Response.Status.CREATED)
            .entity(Map.of(
                "id", invitation.id,
                "expiresAt", invitation.expiresAt.toString()
            ))
            .build();
    }

    private boolean hasPermission(User actor, String tenantId) {
        if (actor == null) return false;
        if (!actor.tenantId.equals(tenantId)) return false;

        // Check if actor is ADMIN or OWNER
        return actor.role == Role.ADMIN || actor.role == Role.OWNER;
    }

    private long countOccupiedSeats(String tenantId) {
        long userCount = store.usersOfTenant(tenantId).stream()
            .filter(user -> user.status != UserStatus.DELETED)
            .count();

        long invitationCount = store.invitationsOfTenant(tenantId).stream()
            .filter(invitation -> invitation.status == InvitationStatus.PENDING)
            .count();

        return userCount + invitationCount;
    }

    private int getMaxUsers(Tenant tenant) {
        if (tenant.plan == Plan.ENTERPRISE) {
            return Integer.MAX_VALUE;
        }
        return tenant.plan == Plan.FREE ? 5 : 50;
    }
}

record Request(String email, Role role) {}
```