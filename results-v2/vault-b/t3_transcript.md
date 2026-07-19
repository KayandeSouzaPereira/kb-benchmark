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

ACTION: read 202602041130-reenvio-de-convites.md

---

## user

RESULT (6 ações restantes):
# 202602041130 Reenvio de convites

Reenvio é ADMIN+, como toda mutação ([[202601051030-papeis-do-tenant]]).

- **Máximo 3 reenvios por convite.** O 4º → 422 `RESEND_LIMIT_REACHED`,
  sem alterar nada. (Anti-spam: reclamação de destinatários bombardeados.)
- Cada reenvio incrementa `resendCount` e **reseta `expiresAt` para agora
  + 72h** — a janela de [[202602041100-expiracao-de-convites-72h]] recomeça.
- Reenviar convite já expirado é permitido e o **reativa** (nova janela).
  Não faz sentido obrigar a recriar o convite.
- Reenvio NÃO passa pela checagem de limite de plano — o assento já está
  reservado ([[202605021430-convites-pendentes-contam]]).
- Audita `INVITATION_RESENT` ([[202601201300-auditoria-de-mutacoes]]).


---

## assistant

ACTION: read 202601201300-auditoria-de-mutacoes.md

---

## user

RESULT (5 ações restantes):
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

ACTION: read 202602041100-expiracao-de-convites-72h.md

---

## user

RESULT (4 ações restantes):
# 202602041100 Convite expira em 72 horas

Todo convite nasce PENDING com `resendCount = 0` e expira 72 horas depois
da criação: `expiresAt = createdAt + 72h`.

Por que 72 e não 24/48: dados do funil mostraram que 31% das aceitações
acontecem no 2º ou 3º dia (convites corporativos esperam aprovação interna).

Aceitar um convite já expirado → 410 `INVITATION_EXPIRED`. Aceitação cria o
usuário ACTIVE e marca o convite ACCEPTED.

Quem pode criar: ADMIN+ ([[202601051030-papeis-do-tenant]]), respeitando o
limite de assentos ([[202605021430-convites-pendentes-contam]]).
Toda criação audita `USER_INVITED` ([[202601201300-auditoria-de-mutacoes]]).
Reenvio muda a expiração: [[202602041130-reenvio-de-convites]].


---

## assistant

ACTION: read 202601051030-papeis-do-tenant.md

---

## user

RESULT (3 ações restantes):
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

ACTION: read 202601201330-codigos-de-erro-da-api.md

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

ACTION: read 202602101415-protecao-do-owner.md

---

## user

RESULT (0 ações restantes):
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

        // 1. Verificar se o ator pertence ao tenant
        if (!store.usersOfTenant(tenantId).stream()
                .anyMatch(user -> user.id.equals(actorId))) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // 2. Buscar convite
        Optional<Invitation> invitationOpt = store.invitationsOfTenant(tenantId).stream()
                .filter(invitation -> invitation.id.equals(invitationId))
                .findFirst();

        if (invitationOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        Invitation invitation = invitationOpt.get();

        // 3. Verificar se o convite está em status válido
        if (invitation.status != InvitationStatus.PENDING) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // 4. Verificar se o convite já atingiu o limite de reenvios
        if (invitation.resendCount >= 3) {
            return Response.status(Response.Status.UNPROCESSABLE_ENTITY)
                    .entity("{\"code\": \"RESEND_LIMIT_REACHED\", \"message\": \"Máximo de reenvios atingido\"}")
                    .type(MediaType.APPLICATION_JSON)
                    .build();
        }

        // 5. Verificar se o ator tem permissão para reenviar o convite
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // 6. Verificar se o ator é um ADMIN+ (ADMIN ou OWNER)
        if (!isAdminOrHigher(actor.role)) {
            return Response.status(Response.Status.FORBIDDEN)
                    .entity("{\"code\": \"FORBIDDEN_ROLE\", \"message\": \"Papel insuficiente\"}")
                    .type(MediaType.APPLICATION_JSON)
                    .build();
        }

        // 7. Incrementar resendCount e resetar expiresAt
        invitation.resendCount++;
        invitation.expiresAt = Instant.now().plus(72, ChronoUnit.HOURS);

        // 8. Auditar a ação
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "INVITATION_RESENT";
        auditEntry.targetId = invitationId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "Reenvio de convite";

        store.auditLog.add(auditEntry);

        // 9. Retornar resposta
        return Response.ok()
                .entity(String.format(
                        "{\"resendCount\": %d, \"expiresAt\": \"%s\"}",
                        invitation.resendCount,
                        invitation.expiresAt.toString()
                ))
                .type(MediaType.APPLICATION_JSON)
                .build();
    }

    private boolean isAdminOrHigher(Role role) {
        return role == Role.ADMIN || role == Role.OWNER;
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
[ERROR] /work/vault-b/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[49,51] cannot find symbol
  symbol:   variable UNPROCESSABLE_ENTITY
  location: class jakarta.ws.rs.core.Response.Status
[INFO] 1 error
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.500 s
[INFO] Finished at: 2026-07-19T15:31:30Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure
[ERROR] /work/vault-b/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[49,51] cannot find symbol
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

        // 1. Verificar se o ator pertence ao tenant
        if (!store.usersOfTenant(tenantId).stream()
                .anyMatch(user -> user.id.equals(actorId))) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 2. Buscar convite
        Optional<Invitation> invitationOpt = store.invitationsOfTenant(tenantId).stream()
                .filter(invitation -> invitation.id.equals(invitationId))
                .findFirst();

        if (invitationOpt.isEmpty()) {
            return Response.status(Status.NOT_FOUND).build();
        }

        Invitation invitation = invitationOpt.get();

        // 3. Verificar se o convite está em status válido
        if (invitation.status != InvitationStatus.PENDING) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 4. Verificar se o convite já atingiu o limite de reenvios
        if (invitation.resendCount >= 3) {
            return Response.status(Status.UNPROCESSABLE_ENTITY)
                    .entity("{\"code\": \"RESEND_LIMIT_REACHED\", \"message\": \"Máximo de reenvios atingido\"}")
                    .type(MediaType.APPLICATION_JSON)
                    .build();
        }

        // 5. Verificar se o ator tem permissão para reenviar o convite
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 6. Verificar se o ator é um ADMIN+ (ADMIN ou OWNER)
        if (!isAdminOrHigher(actor.role)) {
            return Response.status(Status.FORBIDDEN)
                    .entity("{\"code\": \"FORBIDDEN_ROLE\", \"message\": \"Papel insuficiente\"}")
                    .type(MediaType.APPLICATION_JSON)
                    .build();
        }

        // 7. Incrementar resendCount e resetar expiresAt
        invitation.resendCount++;
        invitation.expiresAt = Instant.now().plus(72, ChronoUnit.HOURS);

        // 8. Auditar a ação
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "INVITATION_RESENT";
        auditEntry.targetId = invitationId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "Reenvio de convite";

        store.auditLog.add(auditEntry);

        // 9. Retornar resposta
        return Response.ok()
                .entity(String.format(
                        "{\"resendCount\": %d, \"expiresAt\": \"%s\"}",
                        invitation.resendCount,
                        invitation.expiresAt.toString()
                ))
                .type(MediaType.APPLICATION_JSON)
                .build();
    }

    private boolean isAdminOrHigher(Role role) {
        return role == Role.ADMIN || role == Role.OWNER;
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
us
  location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-b/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[63,36] cannot find symbol
  symbol:   variable Status
  location: class com.bench.api.ResendInvitationResource
[INFO] 6 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.463 s
[INFO] Finished at: 2026-07-19T15:32:26Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/vault-b/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[28,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-b/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[37,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-b/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[44,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-b/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[49,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-b/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[58,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.ResendInvitationResource
[ERROR] /work/vault-b/t3/src/main/java/com/bench/api/ResendInvitationResource.java:[63,36] cannot find symbol
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

        // 1. Verificar se o ator pertence ao tenant
        if (!store.usersOfTenant(tenantId).stream()
                .anyMatch(user -> user.id.equals(actorId))) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 2. Buscar convite
        Optional<Invitation> invitationOpt = store.invitationsOfTenant(tenantId).stream()
                .filter(invitation -> invitation.id.equals(invitationId))
                .findFirst();

        if (invitationOpt.isEmpty()) {
            return Response.status(Status.NOT_FOUND).build();
        }

        Invitation invitation = invitationOpt.get();

        // 3. Verificar se o convite está em status válido
        if (invitation.status != InvitationStatus.PENDING) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 4. Verificar se o convite já atingiu o limite de reenvios
        if (invitation.resendCount >= 3) {
            return Response.status(Status.UNPROCESSABLE_ENTITY)
                    .entity("{\"code\": \"RESEND_LIMIT_REACHED\", \"message\": \"Máximo de reenvios atingido\"}")
                    .type(MediaType.APPLICATION_JSON)
                    .build();
        }

        // 5. Verificar se o ator tem permissão para reenviar o convite
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // 6. Verificar se o ator é um ADMIN+ (ADMIN ou OWNER)
        if (!isAdminOrHigher(actor.role)) {
            return Response.status(Status.FORBIDDEN)
                    .entity("{\"code\": \"FORBIDDEN_ROLE\", \"message\": \"Papel insuficiente\"}")
                    .type(MediaType.APPLICATION_JSON)
                    .build();
        }

        // 7. Incrementar resendCount e resetar expiresAt
        invitation.resendCount++;
        invitation.expiresAt = Instant.now().plus(72, ChronoUnit.HOURS);

        // 8. Auditar a ação
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "INVITATION_RESENT";
        auditEntry.targetId = invitationId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "Reenvio de convite";

        store.auditLog.add(auditEntry);

        // 9. Retornar resposta
        return Response.ok()
                .entity(String.format(
                        "{\"resendCount\": %d, \"expiresAt\": \"%s\"}",
                        invitation.resendCount,
                        invitation.expiresAt.toString()
                ))
                .type(MediaType.APPLICATION_JSON)
                .build();
    }

    private boolean isAdminOrHigher(Role role) {
        return role == Role.ADMIN || role == Role.OWNER;
    }
}
```