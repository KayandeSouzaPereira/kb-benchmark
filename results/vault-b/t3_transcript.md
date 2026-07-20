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
202601050900-user-domain-map.md
202601051030-tenant-roles.md
202601080800-lockout-and-passwords.md
202601121000-plan-seat-limits.md
202601201300-mutation-audit-log.md
202601201330-api-error-codes.md
202602041100-invitation-72h-expiry.md
202602041130-invitation-resend.md
202602101415-owner-protection.md
202602101430-last-owner.md
202602151100-tenant-isolation-404.md
202603121015-pending-invites-limit-doubt.md
202603150900-soft-delete-30-days.md
202603150930-who-can-delete-users.md
202604010900-api-and-conventions-map.md
202604111600-frontend-status-badges.md
202605021430-pending-invitations-count.md
202605190800-pricing-ideas.md

---

## assistant

ACTION: read 202602041130-invitation-resend.md
```

---

## user

RESULT (6 actions left):
# 202602041130 Invitation resend

Resend is ADMIN+, like every mutation ([[202601051030-tenant-roles]]).

- **Maximum 3 resends per invitation.** The 4th → 422 `RESEND_LIMIT_REACHED`,
  nothing changes. (Anti-spam: recipients complained about being bombarded.)
- Each resend increments `resendCount` and **resets `expiresAt` to now
  + 72h** — the [[202602041100-invitation-72h-expiry]] window restarts.
- Resending an already-expired invitation is allowed and **reactivates** it
  (fresh window). Forcing people to recreate the invitation makes no sense.
- Resend does NOT go through the plan limit check — the seat is already
  reserved ([[202605021430-pending-invitations-count]]).
- Audits `INVITATION_RESENT` ([[202601201300-mutation-audit-log]]).


---

## assistant

ACTION: read 202601051030-tenant-roles.md
```

---

## user

RESULT (5 actions left):
# 202601051030 Tenant roles

Three roles, strict hierarchy: OWNER > ADMIN > MEMBER.

Administrative mutations — inviting someone, deleting a user, changing a role —
require ADMIN or OWNER ("ADMIN+"). A MEMBER who tries gets 403 with code
`FORBIDDEN_ROLE` (codes in [[202601201330-api-error-codes]]).

But hierarchy is not just "whoever is above rules": the owner has specific
protections that an admin cannot cross → [[202602101415-owner-protection]].

And the actor must belong to the tenant itself → [[202602151100-tenant-isolation-404]].


---

## assistant

ACTION: read 202601201300-mutation-audit-log.md
```

---

## user

RESULT (4 actions left):
# 202601201300 Mutation audit log

Every EFFECTIVE mutation of a user/invitation/role writes an AuditEntry to the
auditLog, in the same operation (no "I'll audit later"). Denied attempts
(403/422) do NOT produce an entry.

Fields: `id` (new UUID), `tenantId`, `actorId` (the `X-Actor-Id`), `action`,
`targetId` (id of the affected resource), `timestamp` (UTC Instant), `details`
(free, optional).

Valid actions — do not invent strings outside this list, compliance dashboards
break:

- `USER_INVITED` (targetId = invitation id)
- `INVITATION_RESENT` (targetId = invitation id)
- `USER_ROLE_CHANGED` (targetId = user id)
- `USER_SOFT_DELETED` (targetId = user id)
- `USER_RESTORED` (targetId = user id)

Links to everything: [[202602041100-invitation-72h-expiry]],
[[202603150900-soft-delete-30-days]], [[202601051030-tenant-roles]].


---

## assistant

ACTION: read 202602151100-tenant-isolation-404.md
```

---

## user

RESULT (3 actions left):
# 202602151100 Tenant isolation answers 404, not 403

The actor (comes in the `X-Actor-Id` header) must belong to the tenant in the
URL.

Detail we almost got wrong: when the actor is from ANOTHER tenant, the response
is **404 `NOT_FOUND`**, not 403. A 403 would confirm to a stranger that the
resource exists — information leak. 404 tells nothing.

Applies to all user and invitation endpoints.
Roles: [[202601051030-tenant-roles]].
Codes: [[202601201330-api-error-codes]].


---

## assistant

ACTION: read 202601201330-api-error-codes.md
```

---

## user

RESULT (2 actions left):
# 202601201330 API error codes

Standard business-error envelope (`code` is a stable contract, `message` is
free):

```json
{ "code": "STABLE_CODE", "message": "human text" }
```

Codes we've settled on:

- 403 `FORBIDDEN_ROLE` — insufficient role ([[202601051030-tenant-roles]])
- 403 `OWNER_PROTECTED` — admin touching an owner ([[202602101415-owner-protection]])
- 409 `LAST_OWNER` — tenant would be left ownerless ([[202602101430-last-owner]])
- 422 `PLAN_LIMIT_EXCEEDED` — seat limit ([[202605021430-pending-invitations-count]])
- 422 `CANNOT_DELETE_SELF` — self-deletion ([[202603150930-who-can-delete-users]])
- 422 `RESEND_LIMIT_REACHED` — 4th resend ([[202602041130-invitation-resend]])
- 410 `INVITATION_EXPIRED` — accepting an expired invite ([[202602041100-invitation-72h-expiry]])
- 404 `NOT_FOUND` — nonexistent OR actor from another tenant ([[202602151100-tenant-isolation-404]])

No stacktraces in the body, ever.


---

## assistant

ACTION: read 202602101415-owner-protection.md
```

---

## user

RESULT (1 actions left):
# 202602101415 Owner protection

Realized today while discussing the Vetrix customer incident: if an ADMIN can
demote or delete an OWNER, a malicious admin takes over the tenant.

Rule we settled on: **an ADMIN never modifies nor deletes an OWNER** — neither
role nor deletion. Response: 403 `OWNER_PROTECTED`. Only an OWNER touches
another OWNER, and only an OWNER promotes someone to OWNER.

This connects to the last-owner edge case: [[202602101430-last-owner]].
Roles in general: [[202601051030-tenant-roles]].


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

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class InvitationResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response resend(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Check if actor exists and belongs to the tenant
        Optional<User> maybeActor = store.findUser(actorId);
        if (maybeActor.isEmpty() || !maybeActor.get().tenantId.equals(tenantId)) {
            return Response.status(404).entity(new ErrorResponse("NOT_FOUND", "Tenant not found")).build();
        }

        User actor = maybeActor.get();

        // Check if actor has ADMIN+ role
        if (actor.role == Role.MEMBER) {
            return Response.status(403)
                    .entity(new ErrorResponse("FORBIDDEN_ROLE", "Insufficient role"))
                    .build();
        }

        // Find the invitation
        Optional<Invitation> maybeInvitation = store.invitations.values().stream()
                .filter(i -> i.id.equals(invitationId) && i.tenantId.equals(tenantId))
                .findFirst();

        if (maybeInvitation.isEmpty()) {
            return Response.status(404)
                    .entity(new ErrorResponse("NOT_FOUND", "Invitation not found"))
                    .build();
        }

        Invitation invitation = maybeInvitation.get();

        // Check resend limit
        if (invitation.resendCount >= 3) {
            return Response.status(422)
                    .entity(new ErrorResponse("RESEND_LIMIT_REACHED", "Maximum resend attempts reached"))
                    .build();
        }

        // Update invitation: increment resend count and reset expiration
        invitation.resendCount += 1;
        invitation.expiresAt = Instant.now().plus(java.time.Duration.ofHours(72));

        // Create audit entry
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "INVITATION_RESENT";
        auditEntry.targetId = invitationId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = null;

        store.auditLog.add(auditEntry);

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