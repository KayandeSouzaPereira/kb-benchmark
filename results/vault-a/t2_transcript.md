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
```

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

ACTION: read produto/regras-usuarios.md
```

---

## user

RESULT (6 ações restantes):
arquivo não encontrado: produto/regras-usuarios.md

---

## assistant

ACTION: grep -r "exclusao" .
```

---

## user

RESULT (5 ações restantes):
nenhum resultado para: -r "exclusao" .

---

## assistant

ACTION: grep -r "usuario" .
```

---

## user

RESULT (4 ações restantes):
nenhum resultado para: -r "usuario" .

---

## assistant

ACTION: ls produto/
```

---

## user

RESULT (3 ações restantes):
planos-e-precos.md

---

## assistant

ACTION: ls dominio/
```

---

## user

RESULT (2 ações restantes):
auditoria.md
autenticacao-e-lockout.md
convites.md
exclusao-de-usuarios.md
limites-de-plano.md
papeis-e-permissoes.md

---

## assistant

ACTION: read dominio/exclusao-de-usuarios.md
```

---

## user

RESULT (1 ações restantes):
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

FILE: src/main/java/com/bench/api/UserResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.time.temporal.ChronoUnit;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            @HeaderParam("X-Actor-Id") String actorId) {
        
        // Verificar se o usuário autenticado existe
        User actor = store.findUser(actorId).orElseThrow(() -> 
            new NotFoundException("Actor not found"));
        
        // Verificar se o usuário a ser excluído existe
        User userToDelete = store.findUser(userId).orElseThrow(() -> 
            new NotFoundException("User not found"));
        
        // Verificar se o usuário pertence ao mesmo tenant
        if (!userToDelete.tenantId.equals(tenantId)) {
            return Response.status(403).build();
        }
        
        // Verificar se o ator pertence ao mesmo tenant
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(403).build();
        }
        
        // Verificar se o ator está tentando excluir a si mesmo
        if (actorId.equals(userId)) {
            return Response.status(422).entity("CANNOT_DELETE_SELF").build();
        }
        
        // Verificar se o ator tem permissão para excluir (ADMIN ou OWNER)
        if (actor.role != Role.ADMIN && actor.role != Role.OWNER) {
            return Response.status(403).build();
        }
        
        // Verificar se o usuário a ser excluído é OWNER
        if (userToDelete.role == Role.OWNER) {
            // Verificar se há pelo menos um OWNER ativo no tenant
            long ownerCount = store.countOwners(tenantId);
            if (ownerCount <= 1) {
                return Response.status(403).entity("OWNER_PROTECTED").build();
            }
        }
        
        // Realizar a exclusão (soft delete)
        Instant now = Instant.now();
        userToDelete.status = UserStatus.DELETED;
        userToDelete.deletedAt = now;
        userToDelete.purgeAt = now.plus(30, ChronoUnit.DAYS);
        
        // Registrar auditoria
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = "audit-" + Instant.now().toEpochMilli();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "USER_SOFT_DELETED";
        auditEntry.targetId = userId;
        auditEntry.timestamp = now;
        auditEntry.details = "User soft deleted by actor " + actorId;
        
        store.auditLog.add(auditEntry);
        
        return Response.noContent().build();
    }
}
```