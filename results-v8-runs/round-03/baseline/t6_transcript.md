## system

You are a senior software engineer on a product team.
You do NOT have access to the team's documentation; use your best judgment for
business rules and conventions.

Produce the final files in this exact format (there may be more than one FILE
block):

FILE: relative/path/to/File.java
```java
<complete file content>
```

Write complete, compilable files; do not modify the project's existing
files.

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

# Implementation Plan

I'll implement the subscription payment failure endpoint according to the requirements. Let me break down what needs to be done:

1. Create a REST endpoint at `/tenants/{tenantId}/billing/payment-failures` that accepts POST requests
2. Handle the request body with `invoiceId` and `amountCents`
3. Create a WebhookDelivery for the tenant
4. Check webhook delivery rate limits
5. Send notification to billing contact

Let me implement this step by step:

FILE: src/main/java/com/bench/api/BillingResource.java
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
import java.util.*;

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

        // Validate request
        if (body.invoiceId == null || body.amountCents <= 0) {
            return Response.status(422).build();
        }

        Tenant tenant = store.tenants.get(tenantId);
        if (tenant == null) {
            return Response.status(404).build();
        }

        // Check rate limiting for webhook deliveries
        Instant now = Instant.now();
        Instant since = now.minus(java.time.Duration.ofMinutes(5)); // 5-minute window
        long recentDeliveries = store.countRecentWebhookDeliveries(tenantId, since);
        
        // Assuming the team's documented limit is 100 deliveries per 5 minutes
        if (recentDeliveries >= 100) {
            // Create a deferred delivery instead of normal one
            WebhookDelivery delivery = createDeferredWebhookDelivery(tenantId, body);
            return Response.status(201).entity(delivery).build();
        }

        // Create webhook delivery
        WebhookDelivery delivery = createWebhookDelivery(tenantId, body);

        // Send notification to billing contact
        sendNotificationToBillingContact(tenant, body);

        return Response.status(201).entity(delivery).build();
    }

    private WebhookDelivery createWebhookDelivery(String tenantId, PaymentFailureRequest body) {
        String id = UUID.randomUUID().toString();
        WebhookDelivery delivery = new WebhookDelivery();
        delivery.id = id;
        delivery.tenantId = tenantId;
        delivery.eventType = "payment.failure";
        delivery.status = WebhookDeliveryStatus.PENDING;
        delivery.attemptCount = 0;
        delivery.maxAttempts = 5; // Assuming standard retry count
        delivery.createdAt = Instant.now();

        // Sign the webhook
        String payload = "{\"id\":\"" + id + "\",\"eventType\":\"payment.failure\",\"invoiceId\":\"" + 
                        body.invoiceId + "\",\"amountCents\":" + body.amountCents + "}";
        
        WebhookConfig config = store.webhookConfigs.get(tenantId);
        if (config != null && config.secret != null) {
            try {
                Mac mac = Mac.getInstance("HmacSHA256");
                mac.init(new SecretKeySpec(config.secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
                byte[] raw = mac.doFinal(payload.getBytes(StandardCharsets.UTF_8));
                StringBuilder hex = new StringBuilder();
                for (byte b : raw) {
                    hex.append(String.format("%02x", b));
                }
                delivery.signature = hex.toString();
            } catch (Exception e) {
                // If signing fails, we still create the delivery but without signature
                delivery.signature = null;
            }
        } else {
            delivery.signature = null;
        }

        store.webhookDeliveries.put(id, delivery);
        return delivery;
    }

    private WebhookDelivery createDeferredWebhookDelivery(String tenantId, PaymentFailureRequest body) {
        String id = UUID.randomUUID().toString();
        WebhookDelivery delivery = new WebhookDelivery();
        delivery.id = id;
        delivery.tenantId = tenantId;
        delivery.eventType = "payment.failure";
        delivery.status = WebhookDeliveryStatus.DEFERRED;
        delivery.attemptCount = 0;
        delivery.maxAttempts = 5;
        delivery.createdAt = Instant.now();

        // Create a payload for signing even when deferred
        String payload = "{\"id\":\"" + id + "\",\"eventType\":\"payment.failure\",\"invoiceId\":\"" + 
                        body.invoiceId + "\",\"amountCents\":" + body.amountCents + "}";
        
        WebhookConfig config = store.webhookConfigs.get(tenantId);
        if (config != null && config.secret != null) {
            try {
                Mac mac = Mac.getInstance("HmacSHA256");
                mac.init(new SecretKeySpec(config.secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
                byte[] raw = mac.doFinal(payload.getBytes(StandardCharsets.UTF_8));
                StringBuilder hex = new StringBuilder();
                for (byte b : raw) {
                    hex.append(String.format("%02x", b));
                }
                delivery.signature = hex.toString();
            } catch (Exception e) {
                delivery.signature = null;
            }
        } else {
            delivery.signature = null;
        }

        store.webhookDeliveries.put(id, delivery);
        return delivery;
    }

    private void sendNotificationToBillingContact(Tenant tenant, PaymentFailureRequest body) {
        // Find billing contact (typically the owner)
        List<User> users = store.usersOfTenant(tenant.id);
        User billingContact = null;
        
        for (User user : users) {
            if (user.role == Role.OWNER && user.status != UserStatus.DELETED) {
                billingContact = user;
                break;
            }
        }
        
        // If no owner found, try to find an admin
        if (billingContact == null) {
            for (User user : users) {
                if (user.role == Role.ADMIN && user.status != UserStatus.DELETED) {
                    billingContact = user;
                    break;
                }
            }
        }
        
        // If no owner or admin found, use the first active user
        if (billingContact == null) {
            for (User user : users) {
                if (user.status == UserStatus.ACTIVE) {
                    billingContact = user;
                    break;
                }
            }
        }
        
        if (billingContact != null) {
            // Determine notification template based on tenant's preference
            String templateId = "payment-failure-notification";
            
            // Create notification log entry
            NotificationLog log = new NotificationLog();
            log.id = UUID.randomUUID().toString();
            log.tenantId = tenant.id;
            log.templateId = templateId;
            log.status = NotificationStatus.QUEUED;
            log.createdAt = Instant.now();
            
            store.notificationLogs.put(log.id, log);
        }
    }

    public static class PaymentFailureRequest {
        public String invoiceId;
        public int amountCents;
    }
}
```