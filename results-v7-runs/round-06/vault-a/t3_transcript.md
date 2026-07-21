## system

You are a senior software engineer on a product team.
The team keeps a knowledge base of Markdown files with the business rules and
conventions. You MUST consult it before writing code, because the
product-specific rules are not obvious.

To explore the knowledge base, reply with ONE single command line per message:

ACTION: ls <path>       (lists files in a directory; use "." for the root)
ACTION: grep <term>     (text search across all notes)
ACTION: read <file>     (reads the content of a note)

After each ACTION you will receive the result. You have at most 8
actions in total — use them well.

When you have what you need, produce the final files in this exact format
(there may be more than one FILE block):

FILE: relative/path/to/File.java
```java
<complete file content>
```

Format rules: never mix ACTION and FILE in the same reply; write complete,
compilable files; do not modify the project's existing files.

---

## user

# Task: resend invitation

Implement the invitation resend endpoint:

```
POST /tenants/{tenantId}/invitations/{invitationId}/resend
Success: 200 with JSON { "resendCount": ..., "expiresAt": "..." }
```

Implement ALL the business rules, permissions, validations and error/audit
conventions the team has defined for invitation resends.


## Existing project (Quarkus 3, Java 21) — do NOT rewrite these classes

Package `com.bench.model`:

```java
public enum Role { OWNER, ADMIN, MEMBER }
public enum UserStatus { INVITED, ACTIVE, SUSPENDED, DELETED }
public enum Plan { FREE, PRO, ENTERPRISE }        // public field: Integer maxUsers (null = unlimited)
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

Package `com.bench.store` — inject with `@Inject`:

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
    public long countOwners(String tenantId);   // owners with status != DELETED
    public void reset();
}
```

Authentication context: the id of the authenticated user (the actor) arrives in
the HTTP header `X-Actor-Id` and matches a `User` in the store. Read it as a
method parameter, exactly like this:

```java
@POST
public Response create(@PathParam("tenantId") String tenantId,
                       SomeRequestBody body,
                       @HeaderParam("X-Actor-Id") String actorId) { ... }
```

Create your REST resources (jakarta.ws.rs) under `src/main/java/com/bench/api/`.
Remember the imports: `com.bench.model.*`, `com.bench.store.InMemoryStore`,
`jakarta.ws.rs.*`, `jakarta.ws.rs.core.*`, `jakarta.inject.Inject`. Use only
classes and methods that exist in the scaffold above.

Known API traps:
- For HTTP statuses outside the standard enum (e.g. 422, 410), use
  `Response.status(422)` — `Response.Status` does NOT have those constants.
- `Instant` has no `plusHours`/`plusDays`; use
  `instant.plus(java.time.Duration.ofHours(n))`.


---

## assistant

ACTION: ls .
```

---

## user

RESULT (7 actions left):
INDEX.md
code-standards/
decisions/
domain/
product/
runbooks/

---

## assistant

ACTION: read domain/invitations.md
```

---

## user

RESULT (6 actions left):
---
type: business-rule
system: user-management
status: active
updated: 2026-05-02
---

# Invitation lifecycle

## Creation

- Only ADMIN+ creates invitations (see
  [roles-and-permissions](roles-and-permissions.md)).
- Respects the plan limit — a pending invitation counts as a seat
  (see [plan-limits](plan-limits.md)).
- **Every invitation expires in 72 hours** from creation:
  `expiresAt = createdAt + 72h`.
- An invitation is born with `status = PENDING` and `resendCount = 0`.
- Mandatory audit: action `USER_INVITED` (see [audit-log](audit-log.md)).

## Resend

- ADMIN+ only.
- **Maximum of 3 resends per invitation.** The 4th returns
  `422 RESEND_LIMIT_REACHED` and changes nothing.
- Each resend **resets the expiry to now + 72h** and increments `resendCount`.
- Resending an already-expired invitation is allowed and **reactivates** it
  (fresh 72h window).
- Mandatory audit: action `INVITATION_RESENT`.

## Acceptance

- Accepting an expired invitation returns `410 INVITATION_EXPIRED`.
- Acceptance creates the user with `status = ACTIVE` and marks the invitation
  as `ACCEPTED`.

## Anti-patterns already observed

- Applying the plan limit on resend (wrong: resend does not create a seat).
- Forgetting to reset `expiresAt` on resend.

## Related

- [roles-and-permissions](roles-and-permissions.md)
- [plan-limits](plan-limits.md)
- [audit-log](audit-log.md)
- [../code-standards/api-error-format.md](../code-standards/api-error-format.md)


---

## assistant

ACTION: read domain/roles-and-permissions.md
```

---

## user

RESULT (5 actions left):
---
type: business-rule
system: user-management
status: active
updated: 2026-05-02
---

# Roles and permissions

Hierarchy within a tenant: `OWNER > ADMIN > MEMBER`.

## Rules

- **Inviting users, deleting users and changing roles requires ADMIN or OWNER**
  (ADMIN+). A MEMBER who tries gets `403 FORBIDDEN_ROLE`.
- **An ADMIN never modifies nor deletes an OWNER** (neither role nor deletion):
  `403 OWNER_PROTECTED`. Only an OWNER may touch another OWNER or promote
  someone to OWNER.
- **A tenant can never be left without an OWNER**: demoting or removing the last
  active OWNER returns `409 LAST_OWNER`. With two or more owners, one owner may
  demote the other.
- **Tenant isolation**: the actor (header `X-Actor-Id`) must belong to the
  tenant in the URL. An actor from another tenant gets `404 NOT_FOUND` — never
  403, so we do not leak the resource's existence.

## When to use / When NOT to use

- Use on every mutation endpoint for users, invitations or roles.
- Do NOT confuse with authentication (login/password) — see
  [authentication-and-lockout](authentication-and-lockout.md).

## Anti-patterns already observed

- Checking the role after mutating state (ALWAYS validate before writing to the
  store).
- Returning 403 for an actor from another tenant (leaks existence; the correct
  answer is 404).

## Related

- [user-deletion](user-deletion.md)
- [invitations](invitations.md)
- [../code-standards/api-error-format.md](../code-standards/api-error-format.md)
- [audit-log](audit-log.md)


---

## assistant

ACTION: read domain/audit-log.md
```

---

## user

RESULT (4 actions left):
---
type: business-rule
system: user-management
status: active
updated: 2026-05-02
---

# Mutation audit log

**Every mutation of a user, invitation or role writes an `AuditEntry`** to
`store.auditLog`, in the same operation (never "later, async").

## Mandatory format

| Field | Value |
|---|---|
| `id` | new UUID |
| `tenantId` | tenant where it happened |
| `actorId` | who performed it (header `X-Actor-Id`) |
| `action` | one of the actions below |
| `targetId` | id of the affected resource (user or invitation) |
| `timestamp` | `Instant.now()` (UTC) |
| `details` | optional, free text |

## Valid actions

- `USER_INVITED` — invitation created (`targetId` = invitation id)
- `INVITATION_RESENT` — invitation resent (`targetId` = invitation id)
- `USER_ROLE_CHANGED` — role changed (`targetId` = user id)
- `USER_SOFT_DELETED` — user deleted (`targetId` = user id)
- `USER_RESTORED` — user restored within the retention window

## Anti-patterns already observed

- Audit only **effective** mutations. Denied attempts (403/422) do NOT produce
  an audit entry.
- Inventing action strings outside the enum above (breaks compliance
  dashboards).

## Related

- [user-deletion](user-deletion.md)
- [invitations](invitations.md)
- [roles-and-permissions](roles-and-permissions.md)


---

## assistant

ACTION: read code-standards/api-error-format.md
```

---

## user

RESULT (3 actions left):
---
type: technical-convention
system: user-management
status: active
updated: 2026-05-02
---

# API error format

Every business error responds JSON with this envelope:

```json
{ "code": "STABLE_CODE", "message": "free human text" }
```

`code` is a stable contract (clients switch on it); `message` may change.

## Code table

| HTTP | `code` | When |
|---|---|---|
| 403 | `FORBIDDEN_ROLE` | Actor without sufficient role (MEMBER attempting a mutation) |
| 403 | `OWNER_PROTECTED` | ADMIN trying to modify/delete an OWNER |
| 409 | `LAST_OWNER` | Operation would leave the tenant without an OWNER |
| 422 | `PLAN_LIMIT_EXCEEDED` | Plan seat limit reached |
| 422 | `CANNOT_DELETE_SELF` | Actor trying to delete their own account |
| 422 | `RESEND_LIMIT_REACHED` | 4th resend of the same invitation |
| 410 | `INVITATION_EXPIRED` | Accepting an expired invitation |
| 404 | `NOT_FOUND` | Nonexistent resource OR actor from another tenant (do not leak existence) |

## When to use / When NOT to use

- Use in every error `Response` of the REST resources.
- Do NOT invent new codes without an ADR; do NOT return stacktraces in the body.

## Related

- [../domain/roles-and-permissions.md](../domain/roles-and-permissions.md)
- [../domain/plan-limits.md](../domain/plan-limits.md)
- [../domain/invitations.md](../domain/invitations.md)


---

## assistant

ACTION: read domain/plan-limits.md
```

---

## user

RESULT (2 actions left):
---
type: business-rule
system: user-management
status: active
updated: 2026-05-02
---

# User seat limits per plan

| Plan | Maximum seats |
|---|---|
| FREE | 5 |
| PRO | 50 |
| ENTERPRISE | unlimited (`maxUsers = null`) |

## What counts as an occupied seat

`occupied seats = tenant users with status != DELETED + invitations with status PENDING`

In other words: **a pending invitation occupies a seat** (decision recorded in
[adr-002](../decisions/adr-002-pending-invitations-count-toward-limit.md)).
INVITED, ACTIVE and SUSPENDED users count; DELETED does not.

## Blocking rule

Creating an invitation when `occupied seats >= plan maximum` returns
`422 PLAN_LIMIT_EXCEEDED` and persists **nothing**.

## When to use / When NOT to use

- Use when creating invitations and when reactivating users.
- Do NOT apply the limit when resending an existing invitation (it does not
  create a new seat).

## Related

- [invitations](invitations.md)
- [../decisions/adr-002-pending-invitations-count-toward-limit.md](../decisions/adr-002-pending-invitations-count-toward-limit.md)
- [../product/plans-and-pricing.md](../product/plans-and-pricing.md)


---

## assistant

ACTION: grep -r "RESEND_LIMIT_REACHED" .
```

---

## user

RESULT (1 actions left):
nenhum resultado para: -r "RESEND_LIMIT_REACHED" .

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
    public Response resend(@PathParam("tenantId") String tenantId,
                           @PathParam("invitationId") String invitationId,
                           @HeaderParam("X-Actor-Id") String actorId) {
        // Find the actor
        User actor = store.findUser(actorId)
                .orElseThrow(() -> new WebApplicationException(Response.status(404).build()));
        
        // Verify tenant isolation
        if (!actor.tenantId.equals(tenantId)) {
            throw new WebApplicationException(Response.status(404).build());
        }

        // Find the invitation
        Invitation invitation = store.invitations.get(invitationId);
        if (invitation == null || !invitation.tenantId.equals(tenantId)) {
            throw new WebApplicationException(Response.status(404).build());
        }

        // Verify actor has permission to resend (ADMIN+)
        if (actor.role == Role.MEMBER) {
            throw new WebApplicationException(
                    Response.status(403).entity(new ErrorResponse("FORBIDDEN_ROLE", "Insufficient role")).build());
        }

        // Check if invitation has reached resend limit
        if (invitation.resendCount >= 3) {
            throw new WebApplicationException(
                    Response.status(422).entity(new ErrorResponse("RESEND_LIMIT_REACHED", "Maximum resends reached")).build());
        }

        // Update invitation
        invitation.resendCount += 1;
        invitation.expiresAt = Instant.now().plus(java.time.Duration.ofHours(72));

        // Create audit entry
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "INVITATION_RESENT";
        audit.targetId = invitationId;
        audit.timestamp = Instant.now();
        store.auditLog.add(audit);

        // Return success response
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