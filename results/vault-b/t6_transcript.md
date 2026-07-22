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

ACTION: read 202606010900-billing-map.md
```

---

## user

RESULT (12 actions left):
# 202606010900 Map — billing & subscriptions

New area, splitting off from the main product map since it's grown enough on
its own.

- Payment failure handling (webhook + notify + rate limit): [[202606010930-payment-failure-handling]]
- Proration: [[202606011000-proration-rules]]
- Invoice numbering: [[202606011030-invoice-numbering]]
- Refunds: [[202606011100-refund-policy]]
- Cancellation: [[202606011130-subscription-cancellation]]
- Trial period: [[202606011200-trial-period]]
- Payment method update: [[202606011230-payment-method-update]]
- Tax handling: [[202606011300-tax-handling]]
- Currency: [[202606011330-currency-support]]
- Credit notes: [[202606011400-credit-notes]]

See also: [[202606020900-webhooks-map]], [[202606030900-notifications-map]],
[[202606040900-rate-limiting-map]].


---

## assistant

ACTION: read 202606010930-payment-failure-handling.md
```

---

## user

RESULT (11 actions left):
# 202606010930 Payment failure handling

When a subscription payment fails, three things need to happen and none of
the rules live here — this note is just the map of what to touch:

1. Record + send a webhook, event type `payment.failed`. Signing:
   [[202606020930-webhook-signing]]. Retry/backoff:
   [[202606021000-webhook-retry-backoff]].
2. Notify the billing contact. Template:
   [[202606030930-email-template-mapping]]. Digest mode decides SENT vs
   QUEUED: [[202606031000-digest-mode-preferences]].
3. Check the tenant's outbound webhook rate limit BEFORE creating the
   delivery: [[202606040930-outbound-webhook-rate-limit]].

Dunning schedule (day 1/3/7 emails, suspend day 10) is a separate scheduled
job, not part of this event handler — not detailing it here.

Related: [[202606011000-proration-rules]], [[202606011130-subscription-cancellation]].


---

## assistant

ACTION: read 202606020930-webhook-signing.md
```

---

## user

RESULT (10 actions left):
# 202606020930 Webhook signing

Every delivery is signed with **HMAC-SHA256** over the raw JSON body, using
the tenant's webhook secret. Store the signature as a lowercase hex string
(64 chars) on the `WebhookDelivery` — no `sha256=` prefix, no colons, just
the raw hex digest.

Sign every delivery including retries (recompute, don't reuse). Never sign
with the API key — that's a different credential from the webhook secret.

Related: [[202606021000-webhook-retry-backoff]],
[[202606010930-payment-failure-handling]].


---

## assistant

ACTION: read 202606021000-webhook-retry-backoff.md
```

---

## user

RESULT (9 actions left):
# 202606021000 Webhook retry / backoff policy

New `WebhookDelivery` always gets **`maxAttempts = 5`**, `attemptCount = 0`.
Status starts `PENDING` — unless the tenant is over the rate limit, then
`DEFERRED` ([[202606040930-outbound-webhook-rate-limit]]).

Backoff schedule for retries: 1min, 5min, 30min, 2h, 12h. After maxAttempts
failures → status `FAILED`, endpoint gets flagged
([[202606021300-endpoint-disabling-on-failures]]).

Related: [[202606020930-webhook-signing]].


---

## assistant

ACTION: read 202606021030-event-type-catalog.md
```

---

## user

RESULT (8 actions left):
# 202606021030 Event type catalog

Dot-separated, resource present-tense + action past-tense: `user.invited`,
`user.deleted`, `payment.failed`, `payment.succeeded`,
`subscription.cancelled`. Never reuse a retired name.


---

## assistant

ACTION: read 202606030930-email-template-mapping.md
```

---

## user

RESULT (7 actions left):
# 202606030930 Email template mapping

Payment failure → **`templateId = "payment_failed_v2"`**. NOT
`payment_failed` (v1) — that one was retired, see
[[202606031330-template-retirement-adr]].

Other mappings while I'm at it: `user.invited` → `invite_v3`,
`subscription.cancelled` → `cancellation_confirmed_v1`.

Related: [[202606031000-digest-mode-preferences]],
[[202606010930-payment-failure-handling]].


---

## assistant

ACTION: read 202606031000-digest-mode-preferences.md
```

---

## user

RESULT (6 actions left):
# 202606031000 Digest mode preferences

Tenant has `notificationDigestMode`: `IMMEDIATE` (default) or
`DAILY_DIGEST`.

- `IMMEDIATE` → notification created with status **`SENT`** right away.
- `DAILY_DIGEST` → created with status **`QUEUED`**, picked up by the
  nightly digest job.

Applies to transactional notifications too, including billing events like
payment failure ([[202606010930-payment-failure-handling]]). Exception:
critical security notifications (password reset, new device) always send
immediately regardless of digest mode — see
[[202606031230-critical-vs-marketing]].

Related: [[202606030930-email-template-mapping]].


---

## assistant

ACTION: read 202606040930-outbound-webhook-rate-limit.md
```

---

## user

RESULT (5 actions left):
# 202606040930 Outbound webhook rate limit

Max **10 webhook deliveries created per tenant in a rolling 60-minute
window**. When creating a new `WebhookDelivery` (any event type), count
existing deliveries for that tenant with `createdAt` in the last 60 min —
if already **≥ 10**, the new delivery gets status **`DEFERRED`** instead of
`PENDING`. Not rejected, not dropped — just deferred behind the limit.

Check happens BEFORE signing, applies to every event type equally. See
[[202606020930-webhook-signing]] and
[[202606010930-payment-failure-handling]].

Related: [[202606041030-per-plan-rate-tiers]] (that one is for the public
API, this one is flat 10/hour regardless of plan — don't mix them up).


---

## assistant

ACTION: read 202606021100-endpoint-registration.md
```

---

## user

RESULT (4 actions left):
# 202606021100 Webhook endpoint registration

ADMIN+ only. URL must be HTTPS (HTTP rejected). One endpoint per tenant
today, no per-event routing yet.


---

## assistant

ACTION: read 202606021300-endpoint-disabling-on-failures.md
```

---

## user

RESULT (3 actions left):
# 202606021300 Disabling endpoints after repeated failures

3 consecutive `FAILED` deliveries (retries exhausted) → endpoint
auto-disabled, in-app notification to admins. Re-enable requires explicit
admin action.

Related: [[202606021000-webhook-retry-backoff]].


---

## assistant

ACTION: read 202606031230-critical-vs-marketing.md
```

---

## user

RESULT (2 actions left):
# 202606031230 Critical vs marketing classification

Critical: security alerts, password reset, payment failure, invitation.
Marketing: product updates, newsletters, upsell. Only marketing respects the
unsubscribe list; critical always sends (subject to digest mode, see
[[202606031000-digest-mode-preferences]]).


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

FILE: src/main/java/com/bench/api/BillingResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Map;
import java.util.UUID;
import java.util.Base64;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;

@Path("/tenants/{tenantId}/billing")
public class BillingResource {

    @Inject
    InMemoryStore store;

    @POST
    @Path("/payment-failures")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response createPaymentFailure(
            @PathParam("tenantId") String tenantId,
            PaymentFailureRequest body,
            @HeaderParam("X-Actor-Id") String actorId) {

        // Find the tenant
        Tenant tenant = store.tenants.get(tenantId);
        if (tenant == null) {
            return Response.status(404).build();
        }

        // Get webhook config for this tenant
        WebhookConfig webhookConfig = store.webhookConfigs.get(tenantId);
        if (webhookConfig == null) {
            // If no webhook config, we still create the notification but don't send webhook
            createNotification(tenant, body);
            return Response.status(201).build();
        }

        // Check rate limit
        Instant oneHourAgo = Instant.now().minus(1, ChronoUnit.HOURS);
        long recentCount = store.countRecentWebhookDeliveries(tenantId, oneHourAgo);

        WebhookDeliveryStatus status = WebhookDeliveryStatus.PENDING;
        if (recentCount >= 10) {
            status = WebhookDeliveryStatus.DEFERRED;
        }

        // Create webhook delivery
        String deliveryId = "webhook_" + UUID.randomUUID().toString();
        WebhookDelivery delivery = new WebhookDelivery();
        delivery.id = deliveryId;
        delivery.tenantId = tenantId;
        delivery.eventType = "payment.failed";
        delivery.status = status;
        delivery.attemptCount = 0;
        delivery.maxAttempts = 5;
        delivery.createdAt = Instant.now();

        // Sign the payload
        String payload = "{\n" +
                "  \"invoiceId\": \"" + body.invoiceId + "\",\n" +
                "  \"amountCents\": " + body.amountCents + "\n" +
                "}";
        String signature = signPayload(payload, webhookConfig.secret);
        delivery.signature = signature;

        // Store the delivery
        store.webhookDeliveries.put(deliveryId, delivery);

        // Create notification
        createNotification(tenant, body);

        // Audit log entry
        AuditEntry audit = new AuditEntry();
        audit.id = "audit_" + UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "payment_failure_created";
        audit.targetId = deliveryId;
        audit.timestamp = Instant.now();
        audit.details = "Payment failure for invoice " + body.invoiceId;
        store.auditLog.add(audit);

        // Return the created delivery
        return Response.status(201).entity(delivery).build();
    }

    private void createNotification(Tenant tenant, PaymentFailureRequest body) {
        String templateId = "payment_failed_v2";
        NotificationLog log = new NotificationLog();
        log.id = "notif_" + UUID.randomUUID().toString();
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

    private String signPayload(String payload, String secret) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKeySpec = new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
            mac.init(secretKeySpec);
            byte[] raw = mac.doFinal(payload.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder();
            for (byte b : raw) {
                hex.append(String.format("%02x", b));
            }
            return hex.toString();
        } catch (Exception e) {
            throw new RuntimeException("Failed to sign payload", e);
        }
    }

    public static class PaymentFailureRequest {
        public String invoiceId;
        public int amountCents;
    }
}
```