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

ACTION: grep "convite"

---

## user

RESULT (6 ações restantes):
202601050900-mapa-dominio-usuarios.md:8: - Limites de assentos: [[202601121000-limites-por-plano]] (atenção à correção em [[202605021430-convites-pendentes-contam]])
202601050900-mapa-dominio-usuarios.md:9: - Convites: [[202602041100-expiracao-de-convites-72h]], [[202602041130-reenvio-de-convites]]
202601121000-limites-por-plano.md:5: Estourar o limite ao criar convite → 422 `PLAN_LIMIT_EXCEEDED`, sem
202601121000-limites-por-plano.md:9: registrei em [[202603121015-convites-e-limite-duvida]] e a resolução final
202601121000-limites-por-plano.md:10: está em [[202605021430-convites-pendentes-contam]].
202601201300-auditoria-de-mutacoes.md:3: Toda mutação EFETIVADA de usuário/convite/papel grava um AuditEntry no
202601201300-auditoria-de-mutacoes.md:14: - `USER_INVITED` (targetId = id do convite)
202601201300-auditoria-de-mutacoes.md:15: - `INVITATION_RESENT` (targetId = id do convite)
202601201300-auditoria-de-mutacoes.md:20: Liga com tudo: [[202602041100-expiracao-de-convites-72h]],
202601201330-codigos-de-erro-da-api.md:15: - 422 `PLAN_LIMIT_EXCEEDED` — limite de assentos ([[202605021430-convites-pendentes-contam]])
202601201330-codigos-de-erro-da-api.md:17: - 422 `RESEND_LIMIT_REACHED` — 4º reenvio ([[202602041130-reenvio-de-convites]])
202601201330-codigos-de-erro-da-api.md:18: - 410 `INVITATION_EXPIRED` — aceitar convite vencido ([[202602041100-expiracao-de-convites-72h]])
202602041100-expiracao-de-convites-72h.md:1: # 202602041100 Convite expira em 72 horas
202602041100-expiracao-de-convites-72h.md:3: Todo convite nasce PENDING com `resendCount = 0` e expira 72 horas depois
202602041100-expiracao-de-convites-72h.md:7: acontecem no 2º ou 3º dia (convites corporativos esperam aprovação interna).
202602041100-expiracao-de-convites-72h.md:9: Aceitar um convite já expirado → 410 `INVITATION_EXPIRED`. Aceitação cria o
202602041100-expiracao-de-convites-72h.md:10: usuário ACTIVE e marca o convite ACCEPTED.
202602041100-expiracao-de-convites-72h.md:13: limite de assentos ([[202605021430-convites-pendentes-contam]]).
202602041100-expiracao-de-convites-72h.md:15: Reenvio muda a expiração: [[202602041130-reenvio-de-convites]].
202602041130-reenvio-de-convites.md:1: # 202602041130 Reenvio de convites
202602041130-reenvio-de-convites.md:5: - **Máximo 3 reenvios por convite.** O 4º → 422 `RESEND_LIMIT_REACHED`,
202602041130-reenvio-de-convites.md:8: + 72h** — a janela de [[202602041100-expiracao-de-convites-72h]] recomeça.
202602041130-reenvio-de-convites.md:9: - Reenviar convite já expirado é permitido e o **reativa** (nova janela).
202602041130-reenvio-de-convites.md:10: Não faz sentido obrigar a recriar o convite.
202602041130-reenvio-de-convites.md:12: reservado ([[202605021430-convites-pendentes-contam]]).
202602151100-isolamento-de-tenant-404.md:9: Vale para todos os endpoints de usuários e convites.
202603121015-convites-e-limite-duvida.md:1: # 202603121015 Convites pendentes contam no limite? (dúvida)
202603121015-convites-e-limite-duvida.md:3: Pensando alto: intuitivamente um convite pendente NÃO deveria contar no
202603121015-convites-e-limite-duvida.md:10: **Superada por [[202605021430-convites-pendentes-contam]] — a decisão final
202604111600-badges-de-status-no-front.md:7: - INVITED → `badge-warning` / "Convite pendente"
202605021430-convites-pendentes-contam.md:1: # 202605021430 Correção: convites pendentes CONTAM no limite
202605021430-convites-pendentes-contam.md:4: minha intuição de [[202603121015-convites-e-limite-duvida]]:
202605021430-convites-pendentes-contam.md:6: **assentos ocupados = usuários com status != DELETED + convites PENDING.**
202605021430-convites-pendentes-contam.md:8: A vaga é reservada no momento do convite. Motivo: sem isso, um tenant FREE
202605021430-convites-pendentes-contam.md:12: Consequência prática: criar convite quando ocupados >= máximo do plano →
202605021430-convites-pendentes-contam.md:15: ([[202602041130-reenvio-de-convites]]).

---

## assistant

ACTION: read 202605021430-convites-pendentes-contam.md

---

## user

RESULT (5 ações restantes):
# 202605021430 Correção: convites pendentes CONTAM no limite

Decisão final com billing e produto (reunião de 2026-05-02), corrigindo
minha intuição de [[202603121015-convites-e-limite-duvida]]:

**assentos ocupados = usuários com status != DELETED + convites PENDING.**

A vaga é reservada no momento do convite. Motivo: sem isso, um tenant FREE
convidava 30 pessoas e todas aceitavam (bug do incidente #482). Bloquear na
aceitação seria UX horrível.

Consequência prática: criar convite quando ocupados >= máximo do plano →
422 `PLAN_LIMIT_EXCEEDED` ([[202601121000-limites-por-plano]]).
Reenvio NÃO passa por essa checagem — não cria assento novo
([[202602041130-reenvio-de-convites]]).


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

ACTION: read 202602041130-reenvio-de-convites.md

---

## user

RESULT (3 ações restantes):
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

ACTION: read 202601051030-papeis-do-tenant.md

---

## user

RESULT (2 ações restantes):
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

FILE: com/bench/api/InvitationResource.java
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

@Path("/tenants/{tenantId}/invitations")
public class InvitationResource {
    @Inject
    InMemoryStore store;

    @POST
    public Response createInvitation(
        @PathParam("tenantId") String tenantId,
        @HeaderParam("X-Actor-Id") String actorId,
        @RequestBody InvitationRequestBody requestBody
    ) {
        // Verificar se o ator pertence ao tenant
        if (!store.usersOfTenant(tenantId).stream()
                .anyMatch(user -> user.id.equals(actorId))) {
            return Response.status(Status.NOT_FOUND).build();
        }

        // Verificar se o ator tem permissão para criar convites
        if (!hasPermissionToCreateInvitation(tenantId, actorId)) {
            return Response.status(Status.FORBIDDEN).build();
        }

        // Verificar limite de assentos
        if (isPlanLimitExceeded(tenantId)) {
            return Response.status(Status.UNPROCESSABLE_ENTITY)
                .entity(Map.of("error", "PLAN_LIMIT_EXCEEDED"))
                .build();
        }

        // Criar convite
        Invitation invitation = createInvitation(tenantId, requestBody.email, requestBody.role);

        // Auditar ação
        store.auditLog.add(new AuditEntry(
            UUID.randomUUID().toString(),
            tenantId,
            actorId,
            "USER_INVITED",
            invitation.id,
            Instant.now(),
            "Invitation created for " + requestBody.email
        ));

        return Response.status(Status.CREATED)
            .entity(Map.of(
                "id", invitation.id,
                "expiresAt", invitation.expiresAt.toString()
            ))
            .build();
    }

    private boolean hasPermissionToCreateInvitation(String tenantId, String actorId) {
        Tenant tenant = store.tenants.get(tenantId);
        User actor = store.findUser(actorId).orElse(null);

        if (actor == null) {
            return false;
        }

        if (actor.status == UserStatus.DELETED) {
            return false;
        }

        if (tenant == null) {
            return false;
        }

        // Verificar se o ator é OWNER ou ADMIN
        if (actor.role == Role.OWNER || actor.role == Role.ADMIN) {
            return true;
        }

        return false;
    }

    private boolean isPlanLimitExceeded(String tenantId) {
        Tenant tenant = store.tenants.get(tenantId);
        if (tenant == null) {
            return true;
        }

        int occupiedSeats = (int) store.usersOfTenant(tenantId).stream()
            .filter(user -> user.status != UserStatus.DELETED)
            .count();

        int pendingInvitations = (int) store.invitationsOfTenant(tenantId).stream()
            .filter(invitation -> invitation.status == InvitationStatus.PENDING)
            .count();

        int maxUsers = tenant.plan == Plan.FREE ? 10 : 
                       tenant.plan == Plan.PRO ? 50 : 
                       tenant.plan == Plan.ENTERPRISE ? Integer.MAX_VALUE : 0;

        return occupiedSeats + pendingInvitations >= maxUsers;
    }

    private Invitation createInvitation(String tenantId, String email, Role role) {
        Invitation invitation = new Invitation();
        invitation.id = UUID.randomUUID().toString();
        invitation.tenantId = tenantId;
        invitation.email = email;
        invitation.role = role;
        invitation.createdAt = Instant.now();
        invitation.expiresAt = Instant.now().plus(Duration.ofHours(72));
        invitation.resendCount = 0;
        invitation.status = InvitationStatus.PENDING;

        store.invitations.put(invitation.id, invitation);
        return invitation;
    }
}

record InvitationRequestBody(String email, Role role) {}
```