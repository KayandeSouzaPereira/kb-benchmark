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

ACTION: read 202601051030-tenant-roles.md
```

---

## user

RESULT (6 actions left):
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

ACTION: read 202602101415-owner-protection.md
```

---

## user

RESULT (5 actions left):
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

ACTION: read 202602101430-last-owner.md
```

---

## user

RESULT (4 actions left):
# 202602101430 Last owner

Continuation of [[202602101415-owner-protection]]: a tenant can never be left
without an OWNER.

Any operation that would leave zero active owners — demoting the last owner
(including demoting themselves), removing them, them leaving the tenant —
fails with **409 `LAST_OWNER`**.

With two or more owners the operation goes through: one owner may demote the
other normally.

"Active owner" here = owner with status != DELETED. Relates to
[[202603150900-soft-delete-30-days]].


---

## assistant

ACTION: read 202601201300-mutation-audit-log.md
```

---

## user

RESULT (3 actions left):
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

ACTION: read 202603150900-soft-delete-30-days.md
```

---

## user

RESULT (1 actions left):
# 202603150900 Soft-delete with purge in 30 days

There is no hard delete of users in the product. Deleting =

- `status = DELETED`
- `deletedAt = now`
- `purgeAt = now + 30 days` (the definitive purge job reads this field)
- the record STAYS in the store

Success responds 204 No Content. Restoring within the window is allowed
(audit action `USER_RESTORED`).

30 days was the agreement with legal: compliance wants a minimum 30-day trail,
LGPD killed the 90-day idea. I considered a boolean `deleted` flag and
discarded it — without `purgeAt` the purge job cannot work.

Who can delete: [[202603150930-who-can-delete-users]].
Deletion auditing: [[202601201300-mutation-audit-log]].


---

## assistant

FILE: src/main/java/com/bench/api/UserRoleResource.java
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
public class UserRoleResource {

    @Inject
    InMemoryStore store;

    @PATCH
    public Response changeRole(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            ChangeRoleRequest request,
            @HeaderParam("X-Actor-Id") String actorId) {
        
        // Find the actor user
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(404).entity(new ErrorResponse("NOT_FOUND", "Actor not found")).build();
        }
        User actor = actorOpt.get();

        // Verify actor belongs to the tenant
        if (!tenantId.equals(actor.tenantId)) {
            return Response.status(404).entity(new ErrorResponse("NOT_FOUND", "Actor not found")).build();
        }

        // Find target user
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return Response.status(404).entity(new ErrorResponse("NOT_FOUND", "User not found")).build();
        }
        User targetUser = targetUserOpt.get();

        // Verify target user belongs to the tenant
        if (!tenantId.equals(targetUser.tenantId)) {
            return Response.status(404).entity(new ErrorResponse("NOT_FOUND", "User not found")).build();
        }

        // Check permissions: actor must be ADMIN or OWNER
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return Response.status(403)
                    .entity(new ErrorResponse("FORBIDDEN_ROLE", "Insufficient role"))
                    .build();
        }

        // Check owner protection: ADMIN cannot modify OWNER
        if (actor.role == Role.ADMIN && targetUser.role == Role.OWNER) {
            return Response.status(403)
                    .entity(new ErrorResponse("OWNER_PROTECTED", "Cannot modify owner"))
                    .build();
        }

        // Check last owner rule: if demoting the last owner, fail
        if (targetUser.role == Role.OWNER && request.role != Role.OWNER) {
            long ownerCount = store.countOwners(tenantId);
            if (ownerCount <= 1) {
                return Response.status(409)
                        .entity(new ErrorResponse("LAST_OWNER", "Cannot remove last owner"))
                        .build();
            }
        }

        // Update role
        targetUser.role = request.role;

        // Create audit entry
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "USER_ROLE_CHANGED";
        audit.targetId = userId;
        audit.timestamp = Instant.now();
        audit.details = "Role changed from " + targetUser.role + " to " + request.role;
        store.auditLog.add(audit);

        return Response.ok(targetUser).build();
    }

    public static class ChangeRoleRequest {
        public Role role;
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