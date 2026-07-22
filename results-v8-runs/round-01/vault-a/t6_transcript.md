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

# Task: handle a subscription payment failure

Implement an internal endpoint the billing worker calls when a subscription
payment fails:

```
POST /tenants/{tenantId}/billing/payment-failures
Request JSON: { "invoiceId": "inv_123", "amountCents": 4900 }
Success: 201 with the created WebhookDelivery as JSON
```

This endpoint is called by an internal service, not a human — do not add an
actor/permission check for it.

When a payment failure comes in, the system must:

1. Create and sign a `WebhookDelivery` for this tenant so external systems
   are informed of the failure.
2. Respect whatever limit the team has in place for how many webhook
   deliveries a tenant can receive in a short period — if the tenant is over
   that limit, the delivery should not be treated the same as a normal one.
3. Notify the tenant's billing contact through the appropriate channel and
   template for this kind of event, honoring the tenant's own preference for
   how promptly they want to receive this kind of notification.

Implement ALL the business rules, conventions and thresholds the team has
documented for webhook signing, webhook delivery state, notification
templates, notification delivery timing, and delivery rate limiting. Do not
invent your own values for anything that already has a documented rule
(signing algorithm, retry counts, template ids, thresholds, statuses).


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

ACTION: read webhooks/overview.md
```

---

## user

RESULT (12 actions left):
file not found: webhooks/overview.md

---

## assistant

ACTION: read webhooks/
```

---

## user

RESULT (11 actions left):
file not found: webhooks/

---

## assistant

ACTION: grep -r "WebhookDelivery" .
```

---

## user

RESULT (10 actions left):
INDEX.md:9: | `webhooks/` | Webhook signing, retry/backoff, event catalog, endpoint lifecycle | Before creating or delivering any `WebhookDelivery` |
INDEX.md:11: | `rate-limiting/` | API and webhook rate limits, API keys, abuse detection | Before creating a `WebhookDelivery` or any rate-limited resource |
rate-limiting/outbound-webhook-rate-limit.md:11: 60-minute window**. When creating a new `WebhookDelivery` (any event type),
webhooks/retry-backoff-policy.md:10: Every new `WebhookDelivery` is created with **`maxAttempts = 5`** and
webhooks/webhook-signing.md:12: `WebhookDelivery` record as a lowercase hex string (64 characters), with no

---

## assistant

ACTION: read webhooks/webhook-signing.md
```

---

## user

RESULT (9 actions left):
---
type: technical-convention
system: webhooks
status: active
updated: 2026-05-20
---

# Webhook signing

Every webhook delivery is signed with **HMAC-SHA256** over the raw JSON body,
using the tenant's webhook secret. The signature is stored on the
`WebhookDelivery` record as a lowercase hex string (64 characters), with no
`sha256=` prefix and no colons — just the raw hex digest.

## When to use / When NOT to use

- Sign every delivery, including retries (recompute, do not reuse — the
  payload may include a fresh timestamp).
- Do NOT sign with the tenant's API key; webhook secret and API key are
  separate credentials.

## Related

- [retry-backoff-policy.md](retry-backoff-policy.md)
- [event-type-catalog.md](event-type-catalog.md)
- [../billing/payment-retry-and-webhooks.md](../billing/payment-retry-and-webhooks.md)


---

## assistant

ACTION: read webhooks/retry-backoff-policy.md
```

---

## user

RESULT (8 actions left):
---
type: business-rule
system: webhooks
status: active
updated: 2026-05-20
---

# Webhook retry / backoff policy

Every new `WebhookDelivery` is created with **`maxAttempts = 5`** and
`attemptCount = 0`. Delivery starts in status `PENDING` (or `DEFERRED` if the
tenant is rate-limited — see
[../rate-limiting/outbound-webhook-rate-limit.md](../rate-limiting/outbound-webhook-rate-limit.md)).

Retries use exponential backoff: 1min, 5min, 30min, 2h, 12h. After
`maxAttempts` failed deliveries the record moves to status `FAILED` and the
endpoint is flagged — see
[endpoint-disabling-on-failures.md](endpoint-disabling-on-failures.md).

## Related

- [webhook-signing.md](webhook-signing.md)


---

## assistant

ACTION: read rate-limiting/outbound-webhook-rate-limit.md
```

---

## user

RESULT (7 actions left):
---
type: business-rule
system: rate-limiting
status: active
updated: 2026-05-28
---

# Outbound webhook rate limit

Each tenant may have at most **10 webhook deliveries created in a rolling
60-minute window**. When creating a new `WebhookDelivery` (any event type),
count existing deliveries for that tenant with `createdAt` within the last
60 minutes; if the count is **already at or above 10**, the new delivery is
created with status **`DEFERRED`** instead of `PENDING` (it is NOT rejected
or dropped — it's just queued behind the limit for later processing).

This check happens regardless of the event type, and applies before signing
— see
[../webhooks/webhook-signing.md](../webhooks/webhook-signing.md) and
[../billing/payment-retry-and-webhooks.md](../billing/payment-retry-and-webhooks.md).

## Related

- [per-plan-rate-tiers.md](per-plan-rate-tiers.md)


---

## assistant

ACTION: read billing/payment-retry-and-webhooks.md
```

---

## user

RESULT (6 actions left):
---
type: business-rule
system: billing
status: active
updated: 2026-06-10
---

# Payment failure handling

When a subscription payment fails, the billing worker calls the internal
event pipeline, which must:

1. **Record and send a webhook delivery** with event type `payment.failed`
   to the tenant's registered webhook endpoint. Signing and retry rules are
   NOT defined here — see
   [../webhooks/webhook-signing.md](../webhooks/webhook-signing.md) and
   [../webhooks/retry-backoff-policy.md](../webhooks/retry-backoff-policy.md).
2. **Notify the tenant's billing contact.** Template and delivery timing are
   NOT defined here — see
   [../notifications/email-template-mapping.md](../notifications/email-template-mapping.md)
   and
   [../notifications/digest-mode-preferences.md](../notifications/digest-mode-preferences.md).
3. **Respect the tenant's outbound webhook rate limit** before creating the
   delivery — see
   [../rate-limiting/outbound-webhook-rate-limit.md](../rate-limiting/outbound-webhook-rate-limit.md).

## Dunning schedule (informational — not required for the webhook/notify flow)

Failed payments trigger a dunning e-mail sequence at day 1, day 3 and day 7.
On day 10 the subscription is suspended. This schedule is handled by a
separate scheduled job, not by the payment-failure event handler.

## Related

- [proration-rules.md](proration-rules.md)
- [subscription-cancellation.md](subscription-cancellation.md)


---

## assistant

ACTION: read notifications/email-template-mapping.md
```

---

## user

RESULT (5 actions left):
---
type: technical-convention
system: notifications
status: active
updated: 2026-05-25
---

# Email template mapping

Business events map to template IDs. For payment failure:
**`templateId = "payment_failed_v2"`** (not `payment_failed` — that template
was retired, see [template-catalog-history.md](template-catalog-history.md)).

| Event | Template ID |
|---|---|
| `payment.failed` | `payment_failed_v2` |
| `user.invited` | `invite_v3` |
| `subscription.cancelled` | `cancellation_confirmed_v1` |

## Related

- [digest-mode-preferences.md](digest-mode-preferences.md)
- [../billing/payment-retry-and-webhooks.md](../billing/payment-retry-and-webhooks.md)


---

## assistant

ACTION: read notifications/digest-mode-preferences.md
```

---

## user

RESULT (4 actions left):
---
type: business-rule
system: notifications
status: active
updated: 2026-05-25
---

# Digest mode preferences

Each tenant has a `notificationDigestMode`: `IMMEDIATE` (default) or
`DAILY_DIGEST`.

- `IMMEDIATE` → the notification is created with status **`SENT`** right
  away.
- `DAILY_DIGEST` → the notification is created with status **`QUEUED`** and
  picked up by the nightly digest job instead of sending immediately.

This applies to all transactional notifications, including billing events
like `payment.failed` — see
[../billing/payment-retry-and-webhooks.md](../billing/payment-retry-and-webhooks.md).
Critical security notifications (password reset, new device login) always
send immediately regardless of digest mode — see
[critical-vs-marketing.md](critical-vs-marketing.md).

## Related

- [email-template-mapping.md](email-template-mapping.md)


---

## assistant

ACTION: read domain/tenants.md
```

---

## user

RESULT (3 actions left):
file not found: domain/tenants.md

---

## assistant

ACTION: grep -r "payment.failed" .
```

---

## user

RESULT (2 actions left):
billing/payment-retry-and-webhooks.md:13: 1. **Record and send a webhook delivery** with event type `payment.failed`
notifications/digest-mode-preferences.md:19: like `payment.failed` — see
notifications/email-template-mapping.md:16: | `payment.failed` | `payment_failed_v2` |
webhooks/event-type-catalog.md:11: `user.invited`, `user.deleted`, `payment.failed`, `payment.succeeded`,

---

## assistant

ACTION: read webhooks/event-type-catalog.md
```

---

## user

RESULT (1 actions left):
---
type: technical-convention
system: webhooks
status: active
updated: 2026-04-01
---

# Event type catalog

Dot-separated, present tense on the resource, past tense on the action:
`user.invited`, `user.deleted`, `payment.failed`, `payment.succeeded`,
`subscription.cancelled`. Never reuse a retired event name — add a new one
and deprecate the old.


---

## assistant

FILE: src/main/java/com/bench/api/BillingPaymentFailureResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Map;
import java.util.UUID;

@Path("/tenants/{tenantId}/billing")
public class BillingPaymentFailureResource {

    @Inject
    InMemoryStore store;

    @POST
    @Path("/payment-failures")
    @Produces(MediaType.APPLICATION_JSON)
    @Consumes(MediaType.APPLICATION_JSON)
    public Response create(
            @PathParam("tenantId") String tenantId,
            PaymentFailureRequest body,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Validate request
        if (body.invoiceId == null || body.amountCents <= 0) {
            return Response.status(422).build();
        }

        Tenant tenant = store.tenants.get(tenantId);
        if (tenant == null) {
            return Response.status(404).build();
        }

        // Check webhook rate limit
        Instant windowStart = Instant.now().minus(60, ChronoUnit.MINUTES);
        long recentDeliveries = store.countRecentWebhookDeliveries(tenantId, windowStart);

        WebhookDeliveryStatus initialStatus = WebhookDeliveryStatus.PENDING;
        if (recentDeliveries >= 10) {
            initialStatus = WebhookDeliveryStatus.DEFERRED;
        }

        // Create webhook delivery
        String deliveryId = UUID.randomUUID().toString();
        WebhookDelivery delivery = new WebhookDelivery();
        delivery.id = deliveryId;
        delivery.tenantId = tenantId;
        delivery.eventType = "payment.failed";
        delivery.status = initialStatus;
        delivery.attemptCount = 0;
        delivery.maxAttempts = 5;
        delivery.createdAt = Instant.now();

        // Sign the webhook
        String payload = "{\"invoiceId\":\"" + body.invoiceId + "\",\"amountCents\":" + body.amountCents + "}";
        String signature = signPayload(payload, tenantId);
        delivery.signature = signature;

        // Store the delivery
        store.webhookDeliveries.put(deliveryId, delivery);

        // Notify billing contact
        notifyBillingContact(tenant, body.invoiceId, body.amountCents);

        return Response.status(201).entity(delivery).build();
    }

    private String signPayload(String payload, String tenantId) {
        WebhookConfig config = store.webhookConfigs.get(tenantId);
        if (config == null || config.secret == null) {
            // Return empty signature if no secret
            return "";
        }
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(config.secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            byte[] raw = mac.doFinal(payload.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder();
            for (byte b : raw) {
                hex.append(String.format("%02x", b));
            }
            return hex.toString();
        } catch (Exception e) {
            // In production, this would be logged and handled appropriately
            return "";
        }
    }

    private void notifyBillingContact(Tenant tenant, String invoiceId, int amountCents) {
        // Find billing contact - typically the owner or admin user
        User billingContact = null;
        for (User user : store.usersOfTenant(tenant.id)) {
            if (user.status == UserStatus.ACTIVE && 
                (user.role == Role.OWNER || user.role == Role.ADMIN)) {
                billingContact = user;
                break;
            }
        }

        if (billingContact == null) {
            // No billing contact found, cannot send notification
            return;
        }

        String templateId = "payment_failed_v2";
        
        NotificationLog log = new NotificationLog();
        log.id = UUID.randomUUID().toString();
        log.tenantId = tenant.id;
        log.templateId = templateId;
        log.createdAt = Instant.now();

        if (tenant.notificationDigestMode == NotificationDigestMode.DAILY_DIGEST) {
            log.status = NotificationStatus.QUEUED;
        } else {
            log.status = NotificationStatus.SENT;
        }

        store.notificationLogs.put(log.id, log);
    }

    public static class PaymentFailureRequest {
        public String invoiceId;
        public int amountCents;
    }
}
```