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
202606010900-billing-map.md
202606010930-payment-failure-handling.md
202606011000-proration-rules.md
202606011030-invoice-numbering.md
202606011100-refund-policy.md
202606011130-subscription-cancellation.md
202606011200-trial-period.md
202606011230-payment-method-update.md
202606011300-tax-handling.md
202606011330-currency-support.md
202606011400-credit-notes.md
202606020900-webhooks-map.md
202606020930-webhook-signing.md
202606021000-webhook-retry-backoff.md
202606021030-event-type-catalog.md
202606021100-endpoint-registration.md
202606021130-payload-versioning.md
202606021200-delivery-log-retention.md
202606021230-secret-rotation.md
202606021300-endpoint-disabling-on-failures.md
202606021330-custom-headers.md
202606021400-replay-tool.md
202606030900-notifications-map.md
202606030930-email-template-mapping.md
202606031000-digest-mode-preferences.md
202606031030-unsubscribe-rules.md
202606031100-locale-selection.md
202606031130-sms-fallback-draft.md
202606031200-dedup-window.md
202606031230-critical-vs-marketing.md
202606031300-bounce-handling.md
202606031330-template-retirement-adr.md
202606031400-in-app-retention.md
202606040900-rate-limiting-map.md
202606040930-outbound-webhook-rate-limit.md
202606041000-api-key-rotation.md
202606041030-per-plan-rate-tiers.md
202606041100-burst-allowance.md
202606041130-response-headers.md
202606041200-api-key-scopes.md
202606041230-ip-allowlisting.md
202606041300-internal-service-exemption.md
202606041330-abuse-detection.md
202606041400-reset-window-definition.md
202606050900-sso-map.md
202606050930-saml-jit-provisioning.md
202606051000-domain-claiming.md
202606051030-sso-enforced-tenants.md
202606051100-group-role-mapping.md
202606051130-scim-provisioning.md
202606051200-sso-session-lifetime.md
202606051230-idp-initiated-flow.md
202606051300-break-glass-access.md
202606051330-multiple-idp-draft.md
202606051400-sso-audit-logging.md

---

## assistant

ACTION: read 202603150930-who-can-delete-users.md
```

---

## user

RESULT (12 actions left):
# 202603150930 Who can delete a user

- ADMIN+ of the same tenant ([[202601051030-tenant-roles]],
  [[202602151100-tenant-isolation-404]]).
- An ADMIN does not delete an OWNER → 403 `OWNER_PROTECTED`
  ([[202602101415-owner-protection]]).
- **Nobody deletes themselves** → 422 `CANNOT_DELETE_SELF`. Two reasons:
  prevents accidental orphan tenants and limits stolen-session damage.
- Deletion itself is always soft ([[202603150900-soft-delete-30-days]]) and
  audits `USER_SOFT_DELETED` with targetId = the deleted user
  ([[202601201300-mutation-audit-log]]).


---

## assistant

ACTION: read 202603150900-soft-delete-30-days.md
```

---

## user

RESULT (11 actions left):
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

ACTION: read 202602101415-owner-protection.md
```

---

## user

RESULT (10 actions left):
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

RESULT (9 actions left):
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

RESULT (8 actions left):
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

ACTION: read 202601051030-tenant-roles.md
```

---

## user

RESULT (7 actions left):
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

ACTION: read 202602151100-tenant-isolation-404.md
```

---

## user

RESULT (6 actions left):
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

RESULT (5 actions left):
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

ACTION: read 202603121015-pending-invites-limit-doubt.md
```

---

## user

RESULT (4 actions left):
# 202603121015 Do pending invitations count toward the limit? (doubt)

Thinking out loud: intuitively a pending invitation should NOT count toward
the plan limit — the person hasn't even joined, and punishing the tenant for
an unaccepted e-mail feels unfair. My leaning today is to count only active
users.

To be confirmed with billing/product.

**Superseded by [[202605021430-pending-invitations-count]] — the final decision
was the opposite of what I thought here.**

Context: [[202601121000-plan-seat-limits]].


---

## assistant

ACTION: read 202605021430-pending-invitations-count.md
```

---

## user

RESULT (3 actions left):
# 202605021430 Correction: pending invitations DO count toward the limit

Final decision with billing and product (2026-05-02 meeting), correcting my
intuition from [[202603121015-pending-invites-limit-doubt]]:

**occupied seats = users with status != DELETED + PENDING invitations.**

The seat is reserved at invitation time. Reason: without this, a FREE tenant
invited 30 people and they all accepted (incident #482 bug). Blocking at
acceptance would be horrible UX.

Practical consequence: creating an invitation when occupied >= plan maximum →
422 `PLAN_LIMIT_EXCEEDED` ([[202601121000-plan-seat-limits]]).
Resend does NOT go through this check — it creates no new seat
([[202602041130-invitation-resend]]).


---

## assistant

ACTION: read 202601121000-plan-seat-limits.md
```

---

## user

RESULT (2 actions left):
# 202601121000 Seat limits per plan

FREE = 5 seats, PRO = 50, ENTERPRISE = unlimited (maxUsers null).

Blowing past the limit when creating an invitation → 422
`PLAN_LIMIT_EXCEEDED`, nothing persisted.

What exactly counts as an occupied seat gave me doubts — recorded in
[[202603121015-pending-invites-limit-doubt]] and the final resolution is in
[[202605021430-pending-invitations-count]].

Pricing and commercial positioning: [[202605190800-pricing-ideas]].


---

## assistant

ACTION: read 202604010900-api-and-conventions-map.md
```

---

## user

RESULT (1 actions left):
# 202604010900 Map — API and team conventions

Index note for the technical conventions we've settled on.

- HTTP error format and codes: [[202601201330-api-error-codes]]
- Mandatory audit on mutations: [[202601201300-mutation-audit-log]]
- Frontend status badges: [[202604111600-frontend-status-badges]]

See also the domain map: [[202601050900-user-domain-map]].


---

## assistant

FILE: src/main/java/com/bench/api/UserResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.HeaderParam;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Path("/tenants/{tenantId}/users")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    @Path("/{userId}")
    public Response deleteUser(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            @HeaderParam("X-Actor-Id") String actorId) {
        
        // Find the actor user
        Optional<User> maybeActor = store.findUser(actorId);
        if (maybeActor.isEmpty()) {
            return Response.status(404).build();
        }
        User actor = maybeActor.get();

        // Verify actor belongs to the tenant
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(404).build();
        }

        // Find the user to be deleted
        Optional<User> maybeTargetUser = store.findUser(userId);
        if (maybeTargetUser.isEmpty()) {
            return Response.status(404).build();
        }
        User targetUser = maybeTargetUser.get();

        // Verify target user belongs to the tenant
        if (!targetUser.tenantId.equals(tenantId)) {
            return Response.status(404).build();
        }

        // Check if actor is trying to delete themselves
        if (actor.id.equals(userId)) {
            return Response.status(422)
                    .entity(new ErrorResponse("CANNOT_DELETE_SELF", "Cannot delete yourself"))
                    .build();
        }

        // Check if actor has sufficient role (ADMIN+)
        if (actor.role == Role.MEMBER) {
            return Response.status(403)
                    .entity(new ErrorResponse("FORBIDDEN_ROLE", "Insufficient role"))
                    .build();
        }

        // Check if actor is trying to delete an OWNER
        if (targetUser.role == Role.OWNER && actor.role != Role.OWNER) {
            return Response.status(403)
                    .entity(new ErrorResponse("OWNER_PROTECTED", "Cannot delete an owner"))
                    .build();
        }

        // Check if deleting the last owner would leave tenant without owners
        if (targetUser.role == Role.OWNER) {
            long ownerCount = store.countOwners(tenantId);
            if (ownerCount <= 1) {
                return Response.status(409)
                        .entity(new ErrorResponse("LAST_OWNER", "Cannot remove the last owner"))
                        .build();
            }
        }

        // Perform soft delete
        Instant now = Instant.now();
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = now;
        targetUser.purgeAt = now.plus(java.time.Duration.ofDays(30));

        // Log audit entry
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "USER_SOFT_DELETED";
        auditEntry.targetId = userId;
        auditEntry.timestamp = now;
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