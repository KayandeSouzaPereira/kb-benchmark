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

# Task: change user role

Implement the role change endpoint:

```
PATCH /tenants/{tenantId}/users/{userId}/role
Request JSON:  { "role": "OWNER" | "ADMIN" | "MEMBER" }
Success: 200 with the updated user as JSON
```

Implement ALL the business rules, permissions, validations and error/audit
conventions the team has defined for roles.


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

ACTION: read domain/roles.md
```

---

## user

RESULT (6 actions left):
arquivo não encontrado: domain/roles.md

---

## assistant

ACTION: ls domain/
```

---

## user

RESULT (5 actions left):
audit-log.md
authentication-and-lockout.md
invitations.md
plan-limits.md
roles-and-permissions.md
user-deletion.md

---

## assistant

ACTION: read domain/roles-and-permissions.md
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

RESULT (3 actions left):
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

ACTION: grep -r "LAST_OWNER\|OWNER_PROTECTED\|FORBIDDEN_ROLE" .
```

---

## user

RESULT (1 actions left):
nenhum resultado para: -r "LAST_OWNER\|OWNER_PROTECTED\|FORBIDDEN_ROLE" .

---

## assistant

ACTION: grep -r "409\|403" domain/roles-and-permissions.md
```

---

## user

RESULT (0 actions left):
nenhum resultado para: -r "409\|403" domain/roles-and-permissions.md

---

## assistant

FILE: src/main/java/com/bench/api/UserRoleChangeResource.java
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

@Path("/tenants/{tenantId}/users/{userId}/role")
public class UserRoleChangeResource {

    @Inject
    InMemoryStore store;

    @PATCH
    public Response changeRole(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            ChangeRoleRequest request,
            @HeaderParam("X-Actor-Id") String actorId) {
        
        // Validate request body
        if (request.role == null) {
            return Response.status(422).entity("Role is required").build();
        }

        // Find the actor user
        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(404).build(); // Actor not found - 404, not 403
        }
        User actor = actorOpt.get();

        // Verify actor belongs to the tenant
        if (!tenantId.equals(actor.tenantId)) {
            return Response.status(404).build(); // Tenant mismatch - 404, not 403
        }

        // Find the target user
        Optional<User> targetUserOpt = store.findUser(userId);
        if (!targetUserOpt.isPresent()) {
            return Response.status(404).build();
        }
        User targetUser = targetUserOpt.get();

        // Verify target user belongs to the tenant
        if (!tenantId.equals(targetUser.tenantId)) {
            return Response.status(404).build(); // Tenant mismatch - 404, not 403
        }

        // Check permissions: actor must be ADMIN or OWNER
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return Response.status(403).entity("FORBIDDEN_ROLE").build();
        }

        // Check: ADMIN cannot modify OWNER
        if (actor.role == Role.ADMIN && targetUser.role == Role.OWNER) {
            return Response.status(403).entity("OWNER_PROTECTED").build();
        }

        // Check: Cannot demote the last OWNER
        if (targetUser.role == Role.OWNER && request.role != Role.OWNER) {
            long ownerCount = store.countOwners(tenantId);
            if (ownerCount <= 1) {
                return Response.status(409).entity("LAST_OWNER").build();
            }
        }

        // Perform the role change
        targetUser.role = request.role;

        // Log audit entry
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "USER_ROLE_CHANGED";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "Role changed from " + targetUser.role + " to " + request.role;
        store.auditLog.add(auditEntry);

        return Response.ok(targetUser).build();
    }

    public static class ChangeRoleRequest {
        public Role role;
    }
}
```