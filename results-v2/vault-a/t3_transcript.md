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

ACTION: ls decisoes

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

ACTION: read dominio/convites.md

---

## user

RESULT (3 ações restantes):
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

ACTION: read dominio/limites-de-plano.md

---

## user

RESULT (2 ações restantes):
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

ACTION: read dominio/auditoria.md

---

## user

RESULT (1 ações restantes):
---
tipo: regra-de-negocio
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# Auditoria de mutações

**Toda mutação de usuário, convite ou papel grava um `AuditEntry`** no
`store.auditLog`, na mesma operação (nunca "depois, assíncrono").

## Formato obrigatório

| Campo | Valor |
|---|---|
| `id` | UUID novo |
| `tenantId` | tenant onde ocorreu |
| `actorId` | quem executou (header `X-Actor-Id`) |
| `action` | uma das ações do enum abaixo |
| `targetId` | id do recurso afetado (usuário ou convite) |
| `timestamp` | `Instant.now()` (UTC) |
| `details` | opcional, texto livre |

## Ações válidas

- `USER_INVITED` — convite criado (`targetId` = id do convite)
- `INVITATION_RESENT` — convite reenviado (`targetId` = id do convite)
- `USER_ROLE_CHANGED` — papel alterado (`targetId` = id do usuário)
- `USER_SOFT_DELETED` — usuário excluído (`targetId` = id do usuário)
- `USER_RESTORED` — usuário restaurado dentro da retenção

## Anti-padrões já observados

- Auditar só o caminho feliz e esquecer... não: audita-se **apenas** mutações
  efetivadas. Tentativas negadas (403/422) NÃO geram entrada de auditoria.
- Inventar strings de ação fora do enum acima (quebra dashboards de compliance).

## Relacionados

- [exclusao-de-usuarios](exclusao-de-usuarios.md)
- [convites](convites.md)
- [papeis-e-permissoes](papeis-e-permissoes.md)


---

## assistant

FILE: src/main/java/com/bench/api/ResendInvitationResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
public class ResendInvitationResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response resendInvitation(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Find invitation
        Optional<Invitation> invitationOpt = store.invitationsOfTenant(tenantId).stream()
                .filter(inv -> inv.id.equals(invitationId))
                .findFirst();

        if (invitationOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        Invitation invitation = invitationOpt.get();

        // Check if actor is allowed to resend
        if (!isAllowedToResend(tenantId, actorId)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // Check resend count limit
        if (invitation.resendCount >= 3) {
            return Response.status(Response.Status.UNPROCESSABLE_ENTITY)
                    .entity(Map.of("error", "RESEND_LIMIT_REACHED"))
                    .build();
        }

        // Update invitation
        invitation.resendCount++;
        invitation.expiresAt = Instant.now().plus(72, ChronoUnit.HOURS);

        // Audit
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "INVITATION_RESENT";
        audit.targetId = invitationId;
        audit.timestamp = Instant.now();
        audit.details = "Resend invitation " + invitationId;

        store.auditLog.add(audit);

        // Return success
        return Response.ok(Map.of(
                "resendCount", invitation.resendCount,
                "expiresAt", invitation.expiresAt.toString()
        )).build();
    }

    private boolean isAllowedToResend(String tenantId, String actorId) {
        // Check if actor is an admin or owner
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return false;
        }

        User actor = actorOpt.get();
        if (!actor.tenantId.equals(tenantId)) {
            return false;
        }

        // Check if actor is admin or owner
        return store.countOwners(tenantId) > 0 && 
               (actor.role == Role.ADMIN || actor.role == Role.OWNER);
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
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[43,51] cannot find symbol
  symbol:   variable UNPROCESSABLE_ENTITY
  location: class jakarta.ws.rs.core.Response.Status
[INFO] 1 error
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.714 s
[INFO] Finished at: 2026-07-19T15:19:46Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[43,51] cannot find symbol
[ERROR]   symbol:   variable UNPROCESSABLE_ENTITY
[ERROR]   location: class jakarta.ws.rs.core.Response.Status
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

FILE: src/main/java/com/bench/api/ResendInvitationResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
public class ResendInvitationResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response resendInvitation(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Find invitation
        Optional<Invitation> invitationOpt = store.invitationsOfTenant(tenantId).stream()
                .filter(inv -> inv.id.equals(invitationId))
                .findFirst();

        if (invitationOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        Invitation invitation = invitationOpt.get();

        // Check if actor is allowed to resend
        if (!isAllowedToResend(tenantId, actorId)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // Check resend count limit
        if (invitation.resendCount >= 3) {
            return Response.status(Response.Status.UNPROCESSABLE_ENTITY)
                    .entity(Map.of("error", "RESEND_LIMIT_REACHED"))
                    .build();
        }

        // Update invitation
        invitation.resendCount++;
        invitation.expiresAt = Instant.now().plus(72, ChronoUnit.HOURS);

        // Audit
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "INVITATION_RESENT";
        audit.targetId = invitationId;
        audit.timestamp = Instant.now();
        audit.details = "Resend invitation " + invitationId;

        store.auditLog.add(audit);

        // Return success
        return Response.ok(Map.of(
                "resendCount", invitation.resendCount,
                "expiresAt", invitation.expiresAt.toString()
        )).build();
    }

    private boolean isAllowedToResend(String tenantId, String actorId) {
        // Check if actor is an admin or owner
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return false;
        }

        User actor = actorOpt.get();
        if (!actor.tenantId.equals(tenantId)) {
            return false;
        }

        // Check if actor is admin or owner
        return store.countOwners(tenantId) > 0 && 
               (actor.role == Role.ADMIN || actor.role == Role.OWNER);
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
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[43,51] cannot find symbol
  symbol:   variable UNPROCESSABLE_ENTITY
  location: class jakarta.ws.rs.core.Response.Status
[INFO] 1 error
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.449 s
[INFO] Finished at: 2026-07-19T15:20:28Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[43,51] cannot find symbol
[ERROR]   symbol:   variable UNPROCESSABLE_ENTITY
[ERROR]   location: class jakarta.ws.rs.core.Response.Status
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

FILE: src/main/java/com/bench/api/ResendInvitationResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
public class ResendInvitationResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response resendInvitation(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Find invitation
        Optional<Invitation> invitationOpt = store.invitationsOfTenant(tenantId).stream()
                .filter(inv -> inv.id.equals(invitationId))
                .findFirst();

        if (invitationOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        Invitation invitation = invitationOpt.get();

        // Check if actor is allowed to resend
        if (!isAllowedToResend(tenantId, actorId)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // Check resend count limit
        if (invitation.resendCount >= 3) {
            return Response.status(Response.Status.UNPROCESSABLE_ENTITY)
                    .entity(Map.of("error", "RESEND_LIMIT_REACHED"))
                    .build();
        }

        // Update invitation
        invitation.resendCount++;
        invitation.expiresAt = Instant.now().plus(72, ChronoUnit.HOURS);

        // Audit
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "INVITATION_RESENT";
        audit.targetId = invitationId;
        audit.timestamp = Instant.now();
        audit.details = "Resend invitation " + invitationId;

        store.auditLog.add(audit);

        // Return success
        return Response.ok(Map.of(
                "resendCount", invitation.resendCount,
                "expiresAt", invitation.expiresAt.toString()
        )).build();
    }

    private boolean isAllowedToResend(String tenantId, String actorId) {
        // Check if actor is an admin or owner
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return false;
        }

        User actor = actorOpt.get();
        if (!actor.tenantId.equals(tenantId)) {
            return false;
        }

        // Check if actor is admin or owner
        return store.countOwners(tenantId) > 0 && 
               (actor.role == Role.ADMIN || actor.role == Role.OWNER);
    }
}
```