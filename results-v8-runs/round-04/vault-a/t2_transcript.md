## system

You are a senior software engineer on a product team.
The team keeps a knowledge base of Markdown files with the business rules and
conventions. You MUST consult it before writing code, because the
product-specific rules are not obvious.

To explore the knowledge base, reply with ONE single command line per message:

ACTION: ls <path>       (lists files in a directory; use "." for the root)
ACTION: grep <term>     (text search across all notes)
ACTION: read <file>     (reads the content of a note)

After each ACTION you will receive the result. You have at most 14
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
public class Tenant { public String id, name; public Plan plan;
                      public NotificationDigestMode notificationDigestMode; } // default IMMEDIATE
public class Invitation { public String id, tenantId, email; public Role role;
                          public java.time.Instant createdAt, expiresAt;
                          public int resendCount; public InvitationStatus status; }
public class AuditEntry { public String id, tenantId, actorId, action, targetId;
                          public java.time.Instant timestamp; public String details; }

public enum WebhookDeliveryStatus { PENDING, DEFERRED, DELIVERED, FAILED }
public enum NotificationStatus { SENT, QUEUED }
public enum NotificationDigestMode { IMMEDIATE, DAILY_DIGEST }

public class WebhookConfig { public String tenantId, url, secret; }
public class WebhookDelivery { public String id, tenantId, eventType, signature;
                               public WebhookDeliveryStatus status;
                               public int attemptCount, maxAttempts;
                               public java.time.Instant createdAt; }
public class NotificationLog { public String id, tenantId, templateId;
                               public NotificationStatus status;
                               public java.time.Instant createdAt; }
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
    public Map<String, WebhookConfig> webhookConfigs;
    public Map<String, WebhookDelivery> webhookDeliveries;
    public Map<String, NotificationLog> notificationLogs;
    public long countRecentWebhookDeliveries(String tenantId, java.time.Instant since);
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
- To compute an HMAC-SHA256 hex digest, use the JDK's built-in
  `javax.crypto.Mac`, no extra dependency needed:
  ```java
  Mac mac = Mac.getInstance("HmacSHA256");
  mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
  byte[] raw = mac.doFinal(payload.getBytes(StandardCharsets.UTF_8));
  StringBuilder hex = new StringBuilder();
  for (byte b : raw) hex.append(String.format("%02x", b));
  String signature = hex.toString(); // lowercase hex, 64 chars
  ```


---

## assistant

ACTION: ls .
```

---

## user

RESULT (13 actions left):
INDEX.md
billing/
code-standards/
decisions/
domain/
notifications/
product/
rate-limiting/
runbooks/
sso/
webhooks/

---

## assistant

ACTION: read INDEX.md
```

---

## user

RESULT (12 actions left):
# INDEX — Team knowledge base (SaaS user management)

Read this file first. It maps what lives in each folder and when to consult it.

| Folder | Contents | When to consult |
|---|---|---|
| `domain/` | Product business rules: roles and permissions, plan limits, invitations, user deletion, audit log, authentication | Before implementing ANY endpoint or screen that touches users, invitations or roles |
| `billing/` | Subscriptions, payment failures, proration, refunds, invoicing, trials | Before implementing anything related to charges, plans, invoices or payment events |
| `webhooks/` | Webhook signing, retry/backoff, event catalog, endpoint lifecycle | Before creating or delivering any `WebhookDelivery` |
| `notifications/` | Email/in-app notification templates, digest mode, bounce handling | Before sending or queueing any notification |
| `rate-limiting/` | API and webhook rate limits, API keys, abuse detection | Before creating a `WebhookDelivery` or any rate-limited resource |
| `sso/` | SAML/SCIM identity federation, JIT provisioning, break-glass access | Only for SSO/identity-federation work — not needed for billing, webhooks or notifications |
| `code-standards/` | Team technical conventions: API error format, frontend status badges | Whenever returning an HTTP error or rendering status in the UI |
| `decisions/` | ADRs — architectural decisions with discarded alternatives | When a rule seems odd or you want to propose something different |
| `product/` | Product material: plans and pricing | Commercial context; rarely needed for code |
| `runbooks/` | Operational procedures (deploy etc.) | Operations, not development |

**Cross-cutting events** (e.g. a payment failure that must trigger a webhook
AND a notification AND respect a rate limit) touch multiple folders at once —
each relevant note links to the others it depends on under "Related". Follow
those links; do not assume one folder is self-contained for such flows.

## Files in the core folders (domain, code-standards, decisions, product, runbooks)

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

## billing/, webhooks/, notifications/, rate-limiting/, sso/

These folders grew fast and are **not exhaustively indexed here** — each has
around 10 notes. `ls` the specific folder you need; every note's "Related"
section links to the other notes it depends on, so once you find one
relevant note in a folder you can usually navigate to the rest from there
instead of reading the whole folder.


---

## assistant

ACTION: read domain/user-deletion.md
```

---

## user

RESULT (11 actions left):
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

RESULT (10 actions left):
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

RESULT (9 actions left):
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

RESULT (8 actions left):
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

RESULT (7 actions left):
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

ACTION: grep -r "USER_SOFT_DELETED" .
```

---

## user

RESULT (6 actions left):
domain/audit-log.md:30: - `USER_SOFT_DELETED` — user deleted (`targetId` = user id)
domain/user-deletion.md:23: - Mandatory audit: action `USER_SOFT_DELETED` with `targetId` = id of the

---

## assistant

ACTION: ls com/bench/api/
```

---

## user

RESULT (5 actions left):
does not exist: com/bench/api/

---

## assistant

ACTION: mkdir -p com/bench/api
```

---

## user

Invalid format. Reply only with a valid ACTION or with FILE blocks in the specified format.

---

## assistant

ACTION: ls src/main/java/com/bench/api/
```

---

## user

RESULT (4 actions left):
does not exist: src/main/java/com/bench/api/

---

## assistant

ACTION: mkdir -p src/main/java/com/bench/api
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
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.util.UUID;

@Path("/tenants/{tenantId}/users/{userId}")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response delete(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            @HeaderParam("X-Actor-Id") String actorId) {
        
        // Find the actor user
        User actor = store.findUser(actorId).orElse(null);
        if (actor == null || !actor.tenantId.equals(tenantId)) {
            return Response.status(404).build();
        }

        // Find the target user
        User targetUser = store.findUser(userId).orElse(null);
        if (targetUser == null || !targetUser.tenantId.equals(tenantId)) {
            return Response.status(404).build();
        }

        // Check if actor is trying to delete themselves
        if (actorId.equals(userId)) {
            return Response.status(422)
                    .entity(new ErrorResponse("CANNOT_DELETE_SELF", "Cannot delete self"))
                    .build();
        }

        // Check if actor has sufficient role
        if (actor.role == Role.MEMBER) {
            return Response.status(403)
                    .entity(new ErrorResponse("FORBIDDEN_ROLE", "Insufficient role"))
                    .build();
        }

        // Check if actor is trying to delete an OWNER
        if (targetUser.role == Role.OWNER && actor.role != Role.OWNER) {
            return Response.status(403)
                    .entity(new ErrorResponse("OWNER_PROTECTED", "Cannot delete an OWNER"))
                    .build();
        }

        // Check if this would leave the tenant without an OWNER
        if (targetUser.role == Role.OWNER) {
            long ownerCount = store.countOwners(tenantId);
            if (ownerCount <= 1) {
                return Response.status(409)
                        .entity(new ErrorResponse("LAST_OWNER", "Cannot remove the last OWNER"))
                        .build();
            }
        }

        // Perform soft delete
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = Instant.now();
        targetUser.purgeAt = Instant.now().plus(java.time.Duration.ofDays(30));

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