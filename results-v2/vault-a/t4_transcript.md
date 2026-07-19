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

ACTION: read dominio/papeis-e-permissoes.md

---

## user

RESULT (3 ações restantes):
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
        // Validate role
        if (!request.role().equals(Role.OWNER) && 
            !request.role().equals(Role.ADMIN) && 
            !request.role().equals(Role.MEMBER)) {
            return Response.status(Response.Status.BAD_REQUEST).build();
        }

        // Find user
        Optional<User> userOpt = store.findUser(userId);
        if (userOpt.isEmpty()) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        User user = userOpt.get();
        
        // Check if actor belongs to the tenant
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }

        // Check if actor has permission
        if (!hasPermission(actorId, tenantId, user)) {
            return Response.status(Response.Status.FORBIDDEN).build();
        }

        // Check if changing to OWNER
        if (request.role() == Role.OWNER) {
            // Check if tenant has at least one active owner
            if (store.countOwners(tenantId) == 0) {
                return Response.status(Response.Status.CONFLICT)
                              .entity("{\"error\": \"LAST_OWNER\"}")
                              .build();
            }
        }

        // Check if changing from OWNER to another role
        if (user.role == Role.OWNER && request.role() != Role.OWNER) {
            // Only OWNER can change other OWNERS
            if (!store.findUser(actorId).isPresent() || 
                store.findUser(actorId).get().role != Role.OWNER) {
                return Response.status(Response.Status.FORBIDDEN)
                          .entity("{\"error\": \"OWNER_PROTECTED\"}")
                          .build();
            }
        }

        // Check if changing from ADMIN to MEMBER
        if (user.role == Role.ADMIN && request.role() == Role.MEMBER) {
            // Check if there are other owners
            if (store.countOwners(tenantId) < 2) {
                return Response.status(Response.Status.CONFLICT)
                          .entity("{\"error\": \"LAST_OWNER\"}")
                          .build();
            }
        }

        // Update user role
        user.role = request.role();
        
        // Create audit entry
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_ROLE_CHANGED";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = String.format("Role changed from %s to %s", 
                                     user.role, request.role());
        store.auditLog.add(audit);

        return Response.ok(user).build();
    }

    private boolean hasPermission(String actorId, String tenantId, User user) {
        // Actor must be in the same tenant
        if (!user.tenantId.equals(tenantId)) {
            return false;
        }

        // Actor must be ADMIN or OWNER
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null) {
            return false;
        }

        return actor.role == Role.ADMIN || actor.role == Role.OWNER;
    }
}

record RoleChangeRequest(Role role) {}
```