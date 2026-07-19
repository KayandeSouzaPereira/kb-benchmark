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
INDEX.md
decisoes/
dominio/
padroes-codigo/
produto/
runbooks/

---

## assistant

ACTION: ls produto

---

## user

RESULT (6 ações restantes):
planos-e-precos.md

---

## assistant

ACTION: read produto/planos-e-precos.md

---

## user

RESULT (5 ações restantes):
---
tipo: produto
sistema: gestao-usuarios
status: ativo
atualizado: 2026-06-01
---

# Planos e preços

| Plano | Preço | Assentos | Suporte |
|---|---|---|---|
| FREE | R$ 0 | 5 | comunidade |
| PRO | R$ 49/usuário/mês | 50 | e-mail 24h |
| ENTERPRISE | sob consulta | ilimitado | CSM dedicado + SLA |

Upgrade é self-service; downgrade exige que o tenant esteja dentro do limite
do plano de destino. Detalhes técnicos do limite:
[limites-de-plano](../dominio/limites-de-plano.md).


---

## assistant

ACTION: ls dominio

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

ACTION: read dominio/papeis-e-permissoes.md

---

## user

RESULT (2 ações restantes):
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
import java.time.Duration;
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

        // 1. Validate actor belongs to tenant
        User actor = store.findUser(actorId);
        if (actor == null || !actor.tenantId.equals(tenantId)) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 2. Find invitation
        Invitation invitation = store.invitationsOfTenant(tenantId)
                .stream()
                .filter(i -> i.id.equals(invitationId))
                .findFirst()
                .orElse(null);

        if (invitation == null) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 3. Check if invitation is already accepted
        if (invitation.status == InvitationStatus.ACCEPTED) {
            return Response.status(Status.FORBIDDEN).build();
        }

        // 4. Check resend count limit
        if (invitation.resendCount >= 3) {
            return Response.status(Response.Status.UNPROCESSABLE_ENTITY)
                    .entity(Map.of("resendCount", invitation.resendCount, "expiresAt", invitation.expiresAt))
                    .build();
        }

        // 5. Check if actor has permission to resend
        if (!hasResendPermission(actor, tenantId, invitation)) {
            return Response.status(Status.FORBIDDEN).build();
        }

        // 6. Resend invitation
        invitation.resendCount++;
        invitation.expiresAt = Instant.now().plus(Duration.ofHours(72));
        store.invitationsOfTenant(tenantId).remove(invitation);
        store.invitationsOfTenant(tenantId).add(invitation);

        // 7. Create audit entry
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "INVITATION_RESENT";
        audit.targetId = invitationId;
        audit.timestamp = Instant.now();
        audit.details = "Resent invitation with ID " + invitationId;
        store.auditLog.add(audit);

        // 8. Return success response
        return Response.ok()
                .entity(Map.of(
                        "resendCount", invitation.resendCount,
                        "expiresAt", invitation.expiresAt.toString()
                ))
                .build();
    }

    private boolean hasResendPermission(User actor, String tenantId, Invitation invitation) {
        // Check if actor is ADMIN or OWNER
        if (actor.role == Role.ADMIN || actor.role == Role.OWNER) {
            // Check if invitation belongs to the tenant
            return invitation.tenantId.equals(tenantId);
        }
        return false;
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
ABLE_ENTITY
  location: class jakarta.ws.rs.core.Response.Status
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[56,36] cannot find symbol
  symbol:   variable Status
  location: class com.bench.api.ResendInvitationResource
[INFO] 6 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.496 s
[INFO] Finished at: 2026-07-19T16:18:09Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[26,36] incompatible types: java.util.Optional<com.bench.model.User> cannot be converted to com.bench.model.User
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[28,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[39,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[44,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[49,51] cannot find symbol
[ERROR]   symbol:   variable UNPROCESSABLE_ENTITY
[ERROR]   location: class jakarta.ws.rs.core.Response.Status
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[56,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
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
import java.time.Duration;
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

        // 1. Validate actor belongs to tenant
        Optional<User> actorOptional = store.findUser(actorId);
        User actor = actorOptional.orElse(null);
        if (actor == null || !actor.tenantId.equals(tenantId)) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 2. Find invitation
        List<Invitation> invitations = store.invitationsOfTenant(tenantId);
        Invitation invitation = invitations.stream()
                .filter(i -> i.id.equals(invitationId))
                .findFirst()
                .orElse(null);

        if (invitation == null) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 3. Check if invitation is already accepted
        if (invitation.status == InvitationStatus.ACCEPTED) {
            return Response.status(Status.FORBIDDEN).build();
        }

        // 4. Check resend count limit
        if (invitation.resendCount >= 3) {
            return Response.status(Status.UNPROCESSABLE_ENTITY)
                    .entity(Map.of("resendCount", invitation.resend
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
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[51,68] reached end of file while parsing
[INFO] 1 error
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.155 s
[INFO] Finished at: 2026-07-19T16:18:38Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[51,68] reached end of file while parsing
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
import java.time.Duration;
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

        // 1. Validate actor belongs to tenant
        Optional<User> actorOptional = store.findUser(actorId);
        User actor = actorOptional.orElse(null);
        if (actor == null || !actor.tenantId.equals(tenantId)) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 2. Find invitation
        List<Invitation> invitations = store.invitationsOfTenant(tenantId);
        Invitation invitation = invitations.stream()
                .filter(i -> i.id.equals(invitationId))
                .findFirst()
                .orElse(null);

        if (invitation == null) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 3. Check if invitation is already accepted
        if (invitation.status == InvitationStatus.ACCEPTED) {
            return Response.status(Status.FORBIDDEN).build();
        }

        // 4. Check resend count limit
        if (invitation.resendCount >= 3) {
            return Response.status(Status.UNPROCESSABLE_ENTITY)
                    .entity(Map.of("resendCount", invitation.resendCount, "expiresAt", invitation.expiresAt))
                    .build();
        }

        // 5. Check if actor has permission to resend
        if (!hasResendPermission(actor, tenantId, invitation)) {
            return Response.status(Status.FORBIDDEN).build();
        }

        // 6. Resend invitation
        invitation.resendCount++;
        invitation.expiresAt = Instant.now().plus(Duration.ofHours(72));
        store.invitationsOfTenant(tenantId).remove(invitation);
        store.invitationsOfTenant(tenantId).add(invitation);

        // 7. Create audit entry
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "INVITATION_RESENT";
        audit.targetId = invitationId;
        audit.timestamp = Instant.now();
        audit.details = "Resent invitation with ID " + invitationId;
        store.auditLog.add(audit);

        // 8. Return success response
        return Response.ok()
                .entity(Map.of(
                        "resendCount", invitation.resendCount,
                        "expiresAt", invitation.expiresAt.toString()
                ))
                .build();
    }

    private boolean hasResendPermission(User actor, String tenantId, Invitation invitation) {
        // Check if actor is ADMIN or OWNER
        if (actor.role == Role.ADMIN || actor.role == Role.OWNER) {
            // Check if invitation belongs to the tenant
            return invitation.tenantId.equals(tenantId);
        }
        return false;
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
   variable Status
  location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[50,36] cannot find symbol
  symbol:   variable Status
  location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[57,36] cannot find symbol
  symbol:   variable Status
  location: class com.bench.api.ResendInvitationResource
[INFO] 5 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.599 s
[INFO] Finished at: 2026-07-19T16:19:32Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[29,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[40,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[45,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[50,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-a/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[57,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
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
import java.time.Duration;
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

        // 1. Validate actor belongs to tenant
        Optional<User> actorOptional = store.findUser(actorId);
        User actor = actorOptional.orElse(null);
        if (actor == null || !actor.tenantId.equals(tenantId)) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 2. Find invitation
        List<Invitation> invitations = store.invitationsOfTenant(tenantId);
        Invitation invitation = invitations.stream()
                .filter(i -> i.id.equals(invitationId))
                .findFirst()
                .orElse(null);

        if (invitation == null) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 3. Check if invitation is already accepted
        if (invitation.status == InvitationStatus.ACCEPTED) {
            return Response.status(Status.FORBIDDEN).build();
        }

        // 4. Check resend count limit
        if (invitation.resendCount >= 3) {
            return Response.status(Status.UNPROCESSABLE_ENTITY)
                    .entity(Map.of("resendCount", invitation.resendCount, "expiresAt", invitation.expiresAt))
                    .build();
        }

        // 5. Check if actor has permission to resend
        if (!hasResendPermission(actor, tenantId, invitation)) {
            return Response.status(Status.FORBIDDEN).build();
        }

        // 6. Resend invitation
        invitation.resendCount++;
        invitation.expiresAt = Instant.now().plus(Duration.ofHours(72));
        store.invitationsOfTenant(tenantId).remove(invitation);
        store.invitationsOfTenant(tenantId).add(invitation);

        // 7. Create audit entry
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "INVITATION_RESENT";
        audit.targetId = invitationId;
        audit.timestamp = Instant.now();
        audit.details = "Resent invitation with ID " + invitationId;
        store.auditLog.add(audit);

        // 8. Return success response
        return Response.ok()
                .entity(Map.of(
                        "resendCount", invitation.resendCount,
                        "expiresAt", invitation.expiresAt.toString()
                ))
                .build();
    }

    private boolean hasResendPermission(User actor, String tenantId, Invitation invitation) {
        // Check if actor is ADMIN or OWNER
        if (actor.role == Role.ADMIN || actor.role == Role.OWNER) {
            // Check if invitation belongs to the tenant
            return invitation.tenantId.equals(tenantId);
        }
        return false;
    }
}
```