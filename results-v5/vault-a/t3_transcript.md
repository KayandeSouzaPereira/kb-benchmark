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

ACTION: read INDEX.md
```

---

## user

RESULT (6 ações restantes):
# INDEX — Base de conhecimento do time (SaaS de gestão de usuários)

Leia este arquivo primeiro. Ele mapeia o que existe em cada pasta e quando consultar.

| Pasta | Conteúdo | Quando consultar |
|---|---|---|
| `dominio/` | Regras de negócio do produto: papéis e permissões, limites de plano, convites, exclusão de usuários, auditoria, autenticação | Antes de implementar QUALQUER endpoint ou tela que mexa com usuários, convites ou papéis |
| `padroes-codigo/` | Convenções técnicas do time: formato de erros da API, badges de status no frontend | Sempre que for retornar erro HTTP ou renderizar status na UI |
| `decisoes/` | ADRs — decisões arquiteturais com alternativas descartadas | Quando uma regra parecer estranha ou você quiser propor algo diferente |
| `produto/` | Material de produto: planos e preços | Contexto comercial; raramente necessário para código |
| `runbooks/` | Procedimentos operacionais (deploy etc.) | Operação, não desenvolvimento |

## Arquivos por pasta

- `dominio/papeis-e-permissoes.md` — hierarquia OWNER/ADMIN/MEMBER, quem pode fazer o quê, proteções do owner
- `dominio/limites-de-plano.md` — quantos usuários cada plano permite e o que conta no limite
- `dominio/convites.md` — ciclo de vida do convite: expiração, reenvio, aceitação
- `dominio/exclusao-de-usuarios.md` — soft-delete, retenção, quem pode excluir
- `dominio/auditoria.md` — o que auditar e formato obrigatório do AuditEntry
- `dominio/autenticacao-e-lockout.md` — política de senha e bloqueio de conta
- `padroes-codigo/formato-de-erros-api.md` — envelope JSON de erro + tabela de códigos e status HTTP
- `padroes-codigo/badges-de-status-frontend.md` — classes CSS e rótulos PT-BR por status de usuário
- `decisoes/adr-001-soft-delete-com-retencao.md` — por que nunca há hard delete
- `decisoes/adr-002-convites-pendentes-contam-no-limite.md` — por que convite pendente ocupa vaga
- `produto/planos-e-precos.md` — Free / Pro / Enterprise
- `runbooks/deploy-producao.md` — pipeline de deploy


---

## assistant

ACTION: read dominio/convites.md
```

---

## user

RESULT (5 ações restantes):
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
```

---

## user

RESULT (4 ações restantes):
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
```

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

ACTION: read dominio/auditoria.md
```

---

## user

RESULT (2 ações restantes):
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

ACTION: read padroes-codigo/formato-de-erros-api.md
```

---

## user

RESULT (1 ações restantes):
---
tipo: convencao-tecnica
sistema: gestao-usuarios
status: ativo
atualizado: 2026-05-02
---

# Formato de erros da API

Todo erro de negócio responde JSON com este envelope:

```json
{ "code": "CODIGO_ESTAVEL", "message": "texto humano livre" }
```

`code` é contrato estável (clientes fazem switch nele); `message` pode mudar.

## Tabela de códigos

| HTTP | `code` | Quando |
|---|---|---|
| 403 | `FORBIDDEN_ROLE` | Ator sem papel suficiente (MEMBER tentando mutação) |
| 403 | `OWNER_PROTECTED` | ADMIN tentando alterar/excluir um OWNER |
| 409 | `LAST_OWNER` | Operação deixaria o tenant sem OWNER |
| 422 | `PLAN_LIMIT_EXCEEDED` | Limite de assentos do plano atingido |
| 422 | `CANNOT_DELETE_SELF` | Ator tentando excluir a própria conta |
| 422 | `RESEND_LIMIT_REACHED` | 4º reenvio do mesmo convite |
| 410 | `INVITATION_EXPIRED` | Aceitação de convite expirado |
| 404 | `NOT_FOUND` | Recurso inexistente OU ator de outro tenant (não vazar existência) |

## Quando usar / Quando NÃO usar

- Use em todo `Response` de erro dos recursos REST.
- NÃO invente códigos novos sem ADR; NÃO retorne stacktrace no body.

## Relacionados

- [../dominio/papeis-e-permissoes.md](../dominio/papeis-e-permissoes.md)
- [../dominio/limites-de-plano.md](../dominio/limites-de-plano.md)
- [../dominio/convites.md](../dominio/convites.md)


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
import java.util.UUID;

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
public class InvitationResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response resendInvitation(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Verificar se o ator pertence ao tenant
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null || !actor.tenantId.equals(tenantId)) {
            return Response.status(404).entity(new ErrorResponse("NOT_FOUND", "Recurso não encontrado")).build();
        }

        // Verificar se o ator tem permissão (ADMIN ou OWNER)
        if (actor.role == Role.MEMBER) {
            return Response.status(403).entity(new ErrorResponse("FORBIDDEN_ROLE", "Acesso negado")).build();
        }

        // Obter o convite
        Invitation invitation = store.invitations.get(invitationId);
        if (invitation == null || !invitation.tenantId.equals(tenantId)) {
            return Response.status(404).entity(new ErrorResponse("NOT_FOUND", "Convite não encontrado")).build();
        }

        // Verificar se o convite já foi aceito ou revogado
        if (invitation.status == InvitationStatus.ACCEPTED || invitation.status == InvitationStatus.REVOKED) {
            return Response.status(404).entity(new ErrorResponse("NOT_FOUND", "Convite não encontrado")).build();
        }

        // Verificar limite de reenvios
        if (invitation.resendCount >= 3) {
            return Response.status(422)
                    .entity(new ErrorResponse("RESEND_LIMIT_REACHED", "Limite de reenvios atingido"))
                    .build();
        }

        // Atualizar o convite: resetar expiração e incrementar resendCount
        Instant now = Instant.now();
        invitation.expiresAt = now.plus(java.time.Duration.ofHours(72));
        invitation.resendCount++;

        // Registrar auditoria
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "INVITATION_RESENT";
        auditEntry.targetId = invitationId;
        auditEntry.timestamp = now;
        store.auditLog.add(auditEntry);

        // Retornar resposta
        ResendResponse response = new ResendResponse();
        response.resendCount = invitation.resendCount;
        response.expiresAt = invitation.expiresAt;

        return Response.ok(response).build();
    }

    public static class ErrorResponse {
        public String code;
        public String message;

        public ErrorResponse(String code, String message) {
            this.code = code;
            this.message = message;
        }
    }

    public static class ResendResponse {
        public int resendCount;
        public Instant expiresAt;
    }
}
```