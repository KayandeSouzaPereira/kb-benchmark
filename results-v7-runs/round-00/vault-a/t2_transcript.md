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

ACTION: read product/error-codes.md
```

---

## user

RESULT (3 actions left):
arquivo não encontrado: product/error-codes.md

---

## assistant

ACTION: grep -r "CANNOT_DELETE_SELF\|OWNER_PROTECTED" .
```

---

## user

RESULT (2 actions left):
nenhum resultado para: -r "CANNOT_DELETE_SELF\|OWNER_PROTECTED" .

---

## assistant

ACTION: ls code-standards/
```

---

## user

RESULT (1 actions left):
api-error-format.md
frontend-status-badges.md

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
import java.util.List;
import java.util.Optional;
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

        // Find the user to be deleted
        Optional<User> maybeUserToDelete = store.findUser(userId);
        if (maybeUserToDelete.isEmpty()) {
            return Response.status(404).build();
        }
        User userToDelete = maybeUserToDelete.get();

        // Verify tenant isolation - actor must belong to the same tenant
        if (!userToDelete.tenantId.equals(tenantId)) {
            return Response.status(404).build();
        }

        // Find the actor
        Optional<User> maybeActor = store.findUser(actorId);
        if (maybeActor.isEmpty()) {
            return Response.status(404).build();
        }
        User actor = maybeActor.get();

        // Verify actor belongs to the same tenant
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(404).build();
        }

        // Check if actor is trying to delete themselves
        if (actor.id.equals(userId)) {
            return Response.status(422).entity("CANNOT_DELETE_SELF").build();
        }

        // Verify actor has permission to delete users (ADMIN+)
        if (actor.role == Role.MEMBER) {
            return Response.status(403).entity("FORBIDDEN_ROLE").build();
        }

        // Verify actor cannot delete an OWNER
        if (userToDelete.role == Role.OWNER && actor.role != Role.OWNER) {
            return Response.status(403).entity("OWNER_PROTECTED").build();
        }

        // Check if user is already deleted
        if (userToDelete.status == UserStatus.DELETED) {
            return Response.status(404).build();
        }

        // Perform the soft delete
        Instant now = Instant.now();
        Instant purgeAt = now.plus(java.time.Duration.ofDays(30));

        userToDelete.status = UserStatus.DELETED;
        userToDelete.deletedAt = now;
        userToDelete.purgeAt = purgeAt;

        // Create audit entry
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "USER_SOFT_DELETED";
        auditEntry.targetId = userId;
        auditEntry.timestamp = now;
        auditEntry.details = null;

        store.auditLog.add(auditEntry);

        return Response.noContent().build();
    }
}
```