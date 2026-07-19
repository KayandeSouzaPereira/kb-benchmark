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

ACTION: read exclusao-de-usuarios.md

---

## user

RESULT (3 ações restantes):
arquivo não encontrado: exclusao-de-usuarios.md

---

## assistant

ACTION: read dominio/exclusao-de-usuarios.md

---

## user

RESULT (2 ações restantes):
---
tipo: regra-de-negocio
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# Exclusão de usuários (soft-delete)

**Não existe hard delete de usuário neste produto.** Decisão registrada em
[adr-001](../decisoes/adr-001-soft-delete-com-retencao.md).

## Regras

- Excluir um usuário significa: `status = DELETED`, `deletedAt = agora`,
  `purgeAt = agora + 30 dias`. O registro **permanece no store**.
- Somente ADMIN+ exclui, e apenas usuários do próprio tenant.
- ADMIN não pode excluir OWNER: `403 OWNER_PROTECTED`
  (ver [papeis-e-permissoes](papeis-e-permissoes.md)).
- **Ninguém exclui a si mesmo**: `422 CANNOT_DELETE_SELF` — evita tenant órfão
  por acidente e abuso de sessões roubadas.
- Sucesso responde `204 No Content`.
- Auditoria obrigatória: ação `USER_SOFT_DELETED` com `targetId` = id do usuário
  excluído (ver [auditoria](auditoria.md)).

## Quando usar / Quando NÃO usar

- Use em qualquer remoção de usuário disparada pela UI ou API.
- NÃO use para saída voluntária do tenant (fluxo "leave" tem regra própria
  de último owner).

## Anti-padrões já observados

- `store.users.remove(id)` — perde histórico e quebra auditoria. Nunca.
- Esquecer `purgeAt` — o job de purge definitivo depende desse campo.

## Relacionados

- [../decisoes/adr-001-soft-delete-com-retencao.md](../decisoes/adr-001-soft-delete-com-retencao.md)
- [papeis-e-permissoes](papeis-e-permissoes.md)
- [auditoria](auditoria.md)


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

ACTION: read dominio/auditoria.md

---

## user

RESULT (0 ações restantes):
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
            @HeaderParam("X-Actor-Id") String actorId) {

        // Validate actor belongs to the tenant
        if (!store.usersOfTenant(tenantId).stream()
                .anyMatch(user -> user.id.equals(actorId))) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Find user to delete
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User user = userOpt.get();

        // Check if user is self-deletion
        if (user.id.equals(actorId)) {
            return Response.status(Response.Status.UNPROCESSABLE_ENTITY)
                    .entity("Cannot delete self")
                    .build();
        }

        // Check if user is OWNER and actor is ADMIN
        if (user.role == Role.OWNER && user.status != UserStatus.DELETED) {
            return Response.status(Response.Status.FORBIDDEN)
                    .entity("Cannot delete OWNER")
                    .build();
        }

        // Check if actor has sufficient permissions
        if (user.role == Role.MEMBER) {
            return Response.status(Response.Status.FORBIDDEN)
                    .entity("Only ADMIN+ can delete users")
                    .build();
        }

        // Check if tenant has enough seats (for PRO and ENTERPRISE plans)
        Tenant tenant = store.tenants.get(tenantId);
        if (tenant != null && tenant.plan != Plan.FREE) {
            int currentUsers = store.usersOfTenant(tenantId).stream()
                    .filter(u -> u.status != UserStatus.DELETED)
                    .filter(u -> u.role != Role.OWNER)
                    .count();

            int maxUsers = tenant.plan == Plan.PRO ? 50 : Integer.MAX_VALUE;

            if (currentUsers >= maxUsers) {
                return Response.status(Response.Status.FORBIDDEN)
                        .entity("Tenant has reached maximum user limit")
                        .build();
            }
        }

        // Mark user as deleted
        user.status = UserStatus.DELETED;
        user.deletedAt = Instant.now();
        user.purgeAt = Instant.now().plusDays(30);

        // Create audit entry
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_SOFT_DELETED";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "User deleted by " + actorId;

        store.auditLog.add(audit);

        return Response.noContent().build();
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
-resources) @ saas-users ---
[INFO] Copying 1 resource from src/main/resources to target/classes
[INFO] 
[INFO] --- compiler:3.15.0:compile (default-compile) @ saas-users ---
[INFO] Recompiling the module because of changed source code.
[INFO] Compiling 10 source files with javac [debug release 21] to target/classes
[INFO] -------------------------------------------------------------
[ERROR] COMPILATION ERROR : 
[INFO] -------------------------------------------------------------
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[40,51] cannot find symbol
  symbol:   variable UNPROCESSABLE_ENTITY
  location: class jakarta.ws.rs.core.Response.Status
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[65,27] incompatible types: possible lossy conversion from long to int
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[79,37] cannot find symbol
  symbol:   method plusDays(int)
  location: class java.time.Instant
[INFO] 3 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.522 s
[INFO] Finished at: 2026-07-19T15:17:36Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[40,51] cannot find symbol
[ERROR]   symbol:   variable UNPROCESSABLE_ENTITY
[ERROR]   location: class jakarta.ws.rs.core.Response.Status
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[65,27] incompatible types: possible lossy conversion from long to int
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[79,37] cannot find symbol
[ERROR]   symbol:   method plusDays(int)
[ERROR]   location: class java.time.Instant
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
            @HeaderParam("X-Actor-Id") String actorId) {

        // Validate actor belongs to the tenant
        if (!store.usersOfTenant(tenantId).stream()
                .anyMatch(user -> user.id.equals(actorId))) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // Find user to delete
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Status.NOT_FOUND).build();
        }

        User user = userOpt.get();

        // Check if user is self-deletion
        if (user.id.equals(actorId)) {
            return Response.status(Status.UNPROCESSABLE_ENTITY)
                    .entity("Cannot delete self")
                    .build();
        }

        // Check if user is OWNER and actor is ADMIN
        if (user.role == Role.OWNER && user.status != UserStatus.DELETED) {
            return Response.status(Status.FORBIDDEN)
                    .entity("Cannot delete OWNER")
                    .build();
        }

        // Check if actor has sufficient permissions
        if (user.role == Role.MEMBER) {
            return Response.status(Status.FORBIDDEN)
                    .entity("Only ADMIN+ can delete users")
                    .build();
        }

        // Check if tenant has enough seats (for PRO and ENTERPRISE plans)
        Tenant tenant = store.tenants.get(tenantId);
        if (tenant != null && tenant.plan != Plan.FREE) {
            int currentUsers = store.usersOfTenant(tenantId).stream()
                    .filter(u -> u.status != UserStatus.DELETED)
                    .filter(u -> u.role != Role.OWNER)
                    .count();

            int maxUsers = tenant.plan == Plan.PRO ? 50 : Integer.MAX_VALUE;

            if (currentUsers >= maxUsers) {
                return Response.status(Status.FORBIDDEN)
                        .entity("Tenant has reached maximum user limit")
                        .build();
            }
        }

        // Mark user as deleted
        user.status = UserStatus.DELETED;
        user.deletedAt = Instant.now();
        user.purgeAt = Instant.now().plusSeconds(30 * 24 * 60 * 60); // 30 days in seconds

        // Create audit entry
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_SOFT_DELETED";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "User deleted by " + actorId;

        store.auditLog.add(audit);

        return Response.noContent().build();
    }
}
```

---

## user

A compilação/verificação do seu código falhou:

```
rResource.java:[65,27] incompatible types: possible lossy conversion from long to int
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[70,40] cannot find symbol
  symbol:   variable Status
  location: class com.bench.api.UserResource
[INFO] 7 errors 
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  2.445 s
[INFO] Finished at: 2026-07-19T15:18:23Z
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.15.0:compile (default-compile) on project saas-users: Compilation failure: Compilation failure: 
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[27,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[33,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[40,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[47,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[54,36] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.UserResource
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[65,27] incompatible types: possible lossy conversion from long to int
[ERROR] /work/vault-a/t2/src/main/java/com/bench/api/UserResource.java:[70,40] cannot find symbol
[ERROR]   symbol:   variable Status
[ERROR]   location: class com.bench.api.UserResource
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
            @HeaderParam("X-Actor-Id") String actorId) {

        // Validate actor belongs to the tenant
        if (!store.usersOfTenant(tenantId).stream()
                .anyMatch(user -> user.id.equals(actorId))) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // Find user to delete
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Status.NOT_FOUND).build();
        }

        User user = userOpt.get();

        // Check if user is self-deletion
        if (user.id.equals(actorId)) {
            return Response.status(Status.UNPROCESSABLE_ENTITY)
                    .entity("Cannot delete self")
                    .build();
        }

        // Check if user is OWNER and actor is ADMIN
        if (user.role == Role.OWNER && user.status != UserStatus.DELETED) {
            return Response.status(Status.FORBIDDEN)
                    .entity("Cannot delete OWNER")
                    .build();
        }

        // Check if actor has sufficient permissions
        if (user.role == Role.MEMBER) {
            return Response.status(Status.FORBIDDEN)
                    .entity("Only ADMIN+ can delete users")
                    .build();
        }

        // Check if tenant has enough seats (for PRO and ENTERPRISE plans)
        Tenant tenant = store.tenants.get(tenantId);
        if (tenant != null && tenant.plan != Plan.FREE) {
            int currentUsers = store.usersOf
```