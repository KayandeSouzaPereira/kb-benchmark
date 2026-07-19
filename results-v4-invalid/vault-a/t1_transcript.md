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

ACTION: read produto/convites.md
FILE: caminho/relativo/do/Arquivo.java
```java
<conteúdo completo do arquivo>
```

---

## user

RESULT (6 ações restantes):
arquivo não encontrado: produto/convites.md

(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

ACTION: grep -r "convite" .
FILE: caminho/relativo/do/Arquivo.java
```java
<conteúdo completo do arquivo>
```

---

## user

RESULT (5 ações restantes):
nenhum resultado para: -r "convite" .

(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

ACTION: grep -r "invitation" .
FILE: caminho/relativo/do/Arquivo.java
```java
<conteúdo completo do arquivo>
```

---

## user

RESULT (4 ações restantes):
nenhum resultado para: -r "invitation" .

(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

ACTION: ls produto/
FILE: caminho/relativo/do/Arquivo.java
```java
<conteúdo completo do arquivo>
```

---

## user

RESULT (3 ações restantes):
planos-e-precos.md

(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

ACTION: ls dominio/
FILE: caminho/relativo/do/Arquivo.java
```java
<conteúdo completo do arquivo>
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

(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

ACTION: read dominio/convites.md
FILE: caminho/relativo/do/Arquivo.java
```java
<conteúdo completo do arquivo>
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


(Seus blocos FILE foram IGNORADOS porque vieram junto com um ACTION. Termine a exploração e reenvie todos os FILE completos sozinhos na resposta final.)

---

## assistant

FILE: src/main/java/com/bench/api/InvitationResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Path("/tenants/{tenantId}/invitations")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class InvitationResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response createInvitation(
            @PathParam("tenantId") String tenantId,
            InvitationRequest request,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Validação do corpo da requisição
        if (request.email == null || request.email.isEmpty()) {
            return Response.status(422).entity(new ErrorResponse("Email é obrigatório")).build();
        }

        if (request.role == null) {
            return Response.status(422).entity(new ErrorResponse("Role é obrigatória")).build();
        }

        // Verifica se o usuário autenticado existe
        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(401).entity(new ErrorResponse("Usuário não encontrado")).build();
        }
        User actor = actorOpt.get();

        // Verifica se o usuário autenticado pertence ao tenant
        if (!tenantId.equals(actor.tenantId)) {
            return Response.status(403).entity(new ErrorResponse("Acesso negado")).build();
        }

        // Verifica permissões do usuário (somente ADMIN e OWNER podem criar convites)
        if (actor.role != Role.ADMIN && actor.role != Role.OWNER) {
            return Response.status(403).entity(new ErrorResponse("Permissão insuficiente")).build();
        }

        // Verifica se o email já está em uso
        List<User> existingUsers = store.usersOfTenant(tenantId);
        for (User user : existingUsers) {
            if (user.email.equals(request.email)) {
                return Response.status(422).entity(new ErrorResponse("Email já cadastrado")).build();
            }
        }

        // Verifica se o email já foi convidado
        List<Invitation> existingInvitations = store.invitationsOfTenant(tenantId);
        for (Invitation inv : existingInvitations) {
            if (inv.email.equals(request.email) && inv.status == InvitationStatus.PENDING) {
                return Response.status(422).entity(new ErrorResponse("Convite já enviado")).build();
            }
        }

        // Verifica limite de plano
        long ownerCount = store.countOwners(tenantId);
        Tenant tenant = store.tenants.get(tenantId);
        if (tenant != null && tenant.plan.maxUsers != null) {
            long userCount = existingUsers.size() + existingInvitations.size();
            if (userCount >= tenant.plan.maxUsers) {
                return Response.status(422).entity(new ErrorResponse("Limite de usuários atingido")).build();
            }
        }

        // Cria o convite
        Invitation invitation = new Invitation();
        invitation.id = UUID.randomUUID().toString();
        invitation.tenantId = tenantId;
        invitation.email = request.email;
        invitation.role = request.role;
        invitation.createdAt = Instant.now();
        invitation.expiresAt = invitation.createdAt.plus(java.time.Duration.ofHours(72));
        invitation.resendCount = 0;
        invitation.status = InvitationStatus.PENDING;

        // Salva o convite
        store.invitations.put(invitation.id, invitation);

        // Auditoria
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_INVITED";
        audit.targetId = invitation.id;
        audit.timestamp = Instant.now();
        audit.details = String.format("Convite criado para %s com papel %s", invitation.email, invitation.role);
        store.auditLog.add(audit);

        return Response.status(201).entity(invitation).build();
    }

    // Classe auxiliar para o corpo da requisição
    public static class InvitationRequest {
        public String email;
        public Role role;
    }

    // Classe de erro padrão
    public static class ErrorResponse {
        public String message;

        public ErrorResponse(String message) {
            this.message = message;
        }
    }
}
```