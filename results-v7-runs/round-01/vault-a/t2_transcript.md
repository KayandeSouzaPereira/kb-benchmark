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

# Task: delete user

Implement the user deletion endpoint:

```
DELETE /tenants/{tenantId}/users/{userId}
Success: 204 No Content
```

Implement ALL the business rules, permissions, validations and error/audit
conventions the team has defined for user deletion.


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

ACTION: read domain/user-deletion.md
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

# User deletion (soft-delete)

**There is no hard delete of users in this product.** Decision recorded in
[adr-001](../decisions/adr-001-soft-delete-with-retention.md).

## Rules

- Deleting a user means: `status = DELETED`, `deletedAt = now`,
  `purgeAt = now + 30 days`. The record **stays in the store**.
- Only ADMIN+ deletes, and only users of their own tenant.
- An ADMIN cannot delete an OWNER: `403 OWNER_PROTECTED`
  (see [roles-and-permissions](roles-and-permissions.md)).
- **Nobody deletes themselves**: `422 CANNOT_DELETE_SELF` — prevents accidental
  orphan tenants and abuse of stolen sessions.
- Success responds `204 No Content`.
- Mandatory audit: action `USER_SOFT_DELETED` with `targetId` = id of the
  deleted user (see [audit-log](audit-log.md)).

## When to use / When NOT to use

- Use for any user removal triggered by the UI or API.
- Do NOT use for voluntarily leaving a tenant (the "leave" flow has its own
  last-owner rule).

## Anti-patterns already observed

- `store.users.remove(id)` — loses history and breaks auditing. Never.
- Forgetting `purgeAt` — the definitive purge job depends on that field.

## Related

- [../decisions/adr-001-soft-delete-with-retention.md](../decisions/adr-001-soft-delete-with-retention.md)
- [roles-and-permissions](roles-and-permissions.md)
- [audit-log](audit-log.md)


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

ACTION: ls src/main/java/com/bench/api/
```

---

## user

RESULT (2 actions left):
não existe: src/main/java/com/bench/api/

---

## assistant

ACTION: mkdir -p src/main/java/com/bench/api/
```

---

## user

Invalid format. Reply only with a valid ACTION or with FILE blocks in the specified format.

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
import java.util.UUID;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response delete(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Find the actor user
        User actor = store.findUser(actorId)
                .orElseThrow(() -> new WebApplicationException(Response.status(404).build()));

        // Verify tenant isolation - actor must belong to the same tenant
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(404).build();
        }

        // Find the user to be deleted
        User userToDelete = store.findUser(userId)
                .orElseThrow(() -> new WebApplicationException(Response.status(404).build()));

        // Verify tenant isolation - user must belong to the same tenant
        if (!userToDelete.tenantId.equals(tenantId)) {
            return Response.status(404).build();
        }

        // Check if actor is trying to delete themselves
        if (actorId.equals(userId)) {
            return Response.status(422)
                    .entity(new ErrorResponse("CANNOT_DELETE_SELF", "Cannot delete self"))
                    .build();
        }

        // Verify actor has sufficient role (ADMIN or OWNER)
        if (actor.role == Role.MEMBER) {
            return Response.status(403)
                    .entity(new ErrorResponse("FORBIDDEN_ROLE", "Insufficient role"))
                    .build();
        }

        // Check if actor is trying to delete an OWNER
        if (userToDelete.role == Role.OWNER && actor.role != Role.OWNER) {
            return Response.status(403)
                    .entity(new ErrorResponse("OWNER_PROTECTED", "Cannot modify or delete an OWNER"))
                    .build();
        }

        // Soft delete the user
        userToDelete.status = UserStatus.DELETED;
        userToDelete.deletedAt = Instant.now();
        userToDelete.purgeAt = Instant.now().plus(java.time.Duration.ofDays(30));

        // Create audit entry
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "USER_SOFT_DELETED";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        store.auditLog.add(auditEntry);

        return Response.noContent().build();
    }

    // Inner class for error response format
    public static class ErrorResponse {
        public String code;
        public String message;

        public ErrorResponse(String code, String message) {
            this.code = code;
            this.message = message;
        }
    }
}
```