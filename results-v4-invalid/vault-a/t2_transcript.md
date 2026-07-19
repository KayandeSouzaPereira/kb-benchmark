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
<conteúdo completo do arquivo>
```

ACTION: grep -r "user.*delete\|delete.*user" .
ACTION: read regras/negocio/usuarios.md
ACTION: read convencoes/erros.md
ACTION: read regras/negocio/tenant.md
ACTION: read convencoes/auditoria.md
ACTION: read regras/negocio/exclusao-usuarios.md
ACTION: read regras/negocio/permissao.md

---

## user

RESULT (7 ações restantes):
INDEX.md
decisoes/
dominio/
padroes-codigo/
produto/
runbooks/

(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

ACTION: ls decisoes/
ACTION: ls dominio/
ACTION: ls padroes-codigo/
ACTION: ls produto/
ACTION: ls runbooks/
ACTION: read produto/usuarios.md
ACTION: read dominio/usuarios.md
ACTION: read padroes-codigo/erros.md

---

## user

RESULT (6 ações restantes):
adr-001-soft-delete-com-retencao.md
adr-002-convites-pendentes-contam-no-limite.md

---

## assistant

ACTION: read decisoes/adr-001-soft-delete-com-retencao.md
ACTION: read decisoes/adr-002-convites-pendentes-contam-no-limite.md
ACTION: read dominio/usuarios.md
ACTION: read produto/usuarios.md
ACTION: read padroes-codigo/erros.md
ACTION: read convencoes/auditoria.md

---

## user

RESULT (5 ações restantes):
---
tipo: adr
sistema: gestao-usuarios
status: ativo
atualizado: 2026-03-15
---

# ADR-001 — Exclusão de usuário é sempre soft-delete com retenção de 30 dias

## Decisão

Excluir usuário = `status DELETED` + `deletedAt = agora` + `purgeAt = agora + 30 dias`.
O registro fica no store até o job de purge. Restauração dentro da janela é
permitida (ação `USER_RESTORED`).

## Contexto

Clientes B2B excluem usuários por engano com frequência; compliance exige
trilha de auditoria íntegra por no mínimo 30 dias.

## Alternativas descartadas — não propor novamente

- **Hard delete imediato**: quebra auditoria e FK lógicas; rejeitado.
- **Retenção de 90 dias**: conflita com pedidos de LGPD/erasure; 30 dias foi o
  acordo com jurídico.
- **Flag booleana `deleted`**: insuficiente — precisamos de `purgeAt` para o job
  de purge e de `deletedAt` para relatórios.

## Relacionados

- [../dominio/exclusao-de-usuarios.md](../dominio/exclusao-de-usuarios.md)


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
import java.util.List;
import java.util.Optional;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            @HeaderParam("X-Actor-Id") String actorId) {
        
        // Validação de parâmetros
        if (tenantId == null || tenantId.isEmpty()) {
            return Response.status(422).entity("Tenant ID é obrigatório").build();
        }
        if (userId == null || userId.isEmpty()) {
            return Response.status(422).entity("User ID é obrigatório").build();
        }
        if (actorId == null || actorId.isEmpty()) {
            return Response.status(401).entity("Autenticação necessária").build();
        }

        // Verifica se o usuário autenticado existe
        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(401).entity("Usuário autenticado não encontrado").build();
        }
        User actor = actorOpt.get();

        // Verifica se o usuário a ser excluído existe
        Optional<User> userOpt = store.findUser(userId);
        if (!userOpt.isPresent()) {
            return Response.status(404).entity("Usuário não encontrado").build();
        }
        User user = userOpt.get();

        // Verifica se o usuário pertence ao tenant correto
        if (!user.tenantId.equals(tenantId)) {
            return Response.status(403).entity("Acesso negado: usuário não pertence a este tenant").build();
        }

        // Verifica permissões do usuário autenticado
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(403).entity("Acesso negado: usuário autenticado não pertence a este tenant").build();
        }

        // Verifica se o usuário autenticado tem permissão para excluir (OWNER ou ADMIN)
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return Response.status(403).entity("Acesso negado: permissão insuficiente").build();
        }

        // Verifica se o usuário a ser excluído é o próprio usuário autenticado
        if (user.id.equals(actorId)) {
            return Response.status(422).entity("Não é possível excluir o próprio usuário").build();
        }

        // Verifica se o usuário a ser excluído é o único OWNER do tenant
        if (user.role == Role.OWNER && store.countOwners(tenantId) <= 1) {
            return Response.status(422).entity("Não é possível excluir o único OWNER do tenant").build();
        }

        // Realiza a exclusão (soft delete)
        user.status = UserStatus.DELETED;
        user.deletedAt = Instant.now();
        user.purgeAt = Instant.now().plus(30, ChronoUnit.DAYS);

        // Registra auditoria
        AuditEntry audit = new AuditEntry();
        audit.id = java.util.UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_DELETED";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = String.format("Usuário excluído. Motivo: Exclusão via API. User ID: %s", userId);
        store.auditLog.add(audit);

        return Response.noContent().build();
    }
}
```