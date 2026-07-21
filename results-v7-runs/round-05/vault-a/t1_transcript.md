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

# Task: create user invitation

Implement the invitation creation endpoint:

```
POST /tenants/{tenantId}/invitations
Request JSON:  { "email": "person@ex.com", "role": "ADMIN" | "MEMBER" }
Success: 201 with JSON { "id": "...", "expiresAt": "..." }
```

Persist the invitation in the `InMemoryStore`. Implement ALL the business
rules, permissions, validations and error/audit conventions the team has
defined for invitations.


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

ACTION: read INDEX.md
```

---

## user

RESULT (6 actions left):
# INDEX — Team knowledge base (SaaS user management)

Read this file first. It maps what lives in each folder and when to consult it.

| Folder | Contents | When to consult |
|---|---|---|
| `domain/` | Product business rules: roles and permissions, plan limits, invitations, user deletion, audit log, authentication | Before implementing ANY endpoint or screen that touches users, invitations or roles |
| `code-standards/` | Team technical conventions: API error format, frontend status badges | Whenever returning an HTTP error or rendering status in the UI |
| `decisions/` | ADRs — architectural decisions with discarded alternatives | When a rule seems odd or you want to propose something different |
| `product/` | Product material: plans and pricing | Commercial context; rarely needed for code |
| `runbooks/` | Operational procedures (deploy etc.) | Operations, not development |

## Files per folder

- `domain/roles-and-permissions.md` — OWNER/ADMIN/MEMBER hierarchy, who can do what, owner protections
- `domain/plan-limits.md` — how many users each plan allows and what counts toward the limit
- `domain/invitations.md` — invitation lifecycle: expiry, resend, acceptance
- `domain/user-deletion.md` — soft-delete, retention, who can delete
- `domain/audit-log.md` — what to audit and the mandatory AuditEntry format
- `domain/authentication-and-lockout.md` — password policy and account lockout
- `code-standards/api-error-format.md` — JSON error envelope + table of codes and HTTP statuses
- `code-standards/frontend-status-badges.md` — CSS classes and pt-BR labels per user status
- `decisions/adr-001-soft-delete-with-retention.md` — why there is never a hard delete
- `decisions/adr-002-pending-invitations-count-toward-limit.md` — why a pending invite occupies a seat
- `product/plans-and-pricing.md` — Free / Pro / Enterprise
- `runbooks/production-deploy.md` — deploy pipeline


---

## assistant

ACTION: read domain/invitations.md
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

ACTION: read domain/plan-limits.md
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

ACTION: read domain/audit-log.md
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

ACTION: ls src/main/java/com/bench/api/
```

---

## user

RESULT (1 actions left):
não existe: src/main/java/com/bench/api/

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
    public Response create(@PathParam("tenantId") String tenantId,
                           InvitationRequest request,
                           @HeaderParam("X-Actor-Id") String actorId) {
        // Validate request
        if (request.email == null || request.email.isEmpty()) {
            return Response.status(422).entity(new ErrorResponse("EMAIL_REQUIRED", "Email is required")).build();
        }
        if (request.role == null) {
            return Response.status(422).entity(new ErrorResponse("ROLE_REQUIRED", "Role is required")).build();
        }

        // Check if actor exists
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(404).build(); // Actor not found - should return 404 according to roles-and-permissions.md
        }
        User actor = actorOpt.get();

        // Check tenant isolation
        if (!tenantId.equals(actor.tenantId)) {
            return Response.status(404).build();
        }

        // Check permissions
        if (actor.role == Role.MEMBER) {
            return Response.status(403).entity(new ErrorResponse("FORBIDDEN_ROLE", "MEMBER cannot invite users")).build();
        }

        // Check plan limit
        long occupiedSeats = store.usersOfTenant(tenantId).stream()
                .filter(user -> user.status != UserStatus.DELETED)
                .count() + 
                store.invitationsOfTenant(tenantId).stream()
                        .filter(inv -> inv.status == InvitationStatus.PENDING)
                        .count();

        Tenant tenant = store.tenants.get(tenantId);
        if (tenant == null) {
            return Response.status(404).build();
        }

        if (tenant.plan.maxUsers != null && occupiedSeats >= tenant.plan.maxUsers) {
            return Response.status(422).entity(new ErrorResponse("PLAN_LIMIT_EXCEEDED", "Plan limit exceeded")).build();
        }

        // Create invitation
        String invitationId = UUID.randomUUID().toString();
        Instant now = Instant.now();
        Invitation invitation = new Invitation();
        invitation.id = invitationId;
        invitation.tenantId = tenantId;
        invitation.email = request.email;
        invitation.role = request.role;
        invitation.createdAt = now;
        invitation.expiresAt = now.plus(java.time.Duration.ofHours(72));
        invitation.resendCount = 0;
        invitation.status = InvitationStatus.PENDING;

        store.invitations.put(invitationId, invitation);

        // Audit
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_INVITED";
        audit.targetId = invitationId;
        audit.timestamp = Instant.now();
        store.auditLog.add(audit);

        InvitationResponse response = new InvitationResponse();
        response.id = invitationId;
        response.expiresAt = invitation.expiresAt;

        return Response.status(201).entity(response).build();
    }

    public static class InvitationRequest {
        public String email;
        public Role role;
    }

    public static class InvitationResponse {
        public String id;
        public Instant expiresAt;
    }

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