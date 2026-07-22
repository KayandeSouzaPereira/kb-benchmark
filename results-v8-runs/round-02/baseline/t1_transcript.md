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
import java.util.Map;
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
        // Validate request body
        if (request.email == null || request.email.isEmpty()) {
            return Response.status(422).entity(Map.of("error", "Email is required")).build();
        }
        if (request.role == null) {
            return Response.status(422).entity(Map.of("error", "Role is required")).build();
        }

        // Validate tenant exists
        Optional<Tenant> tenantOpt = store.tenants.values().stream()
                .filter(t -> t.id.equals(tenantId))
                .findFirst();
        if (!tenantOpt.isPresent()) {
            return Response.status(404).entity(Map.of("error", "Tenant not found")).build();
        }
        Tenant tenant = tenantOpt.get();

        // Validate actor exists and is active
        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(401).entity(Map.of("error", "Unauthorized")).build();
        }
        User actor = actorOpt.get();
        if (!actor.tenantId.equals(tenantId) || actor.status != UserStatus.ACTIVE) {
            return Response.status(403).entity(Map.of("error", "Forbidden")).build();
        }

        // Check if user is already a member of the tenant
        List<User> users = store.usersOfTenant(tenantId);
        boolean isAlreadyMember = users.stream()
                .anyMatch(u -> u.email.equals(request.email) && u.status != UserStatus.DELETED);
        if (isAlreadyMember) {
            return Response.status(422).entity(Map.of("error", "User is already a member")).build();
        }

        // Check if there's an existing invitation for this email
        List<Invitation> existingInvitations = store.invitationsOfTenant(tenantId);
        boolean hasPendingInvitation = existingInvitations.stream()
                .anyMatch(i -> i.email.equals(request.email) && i.status == InvitationStatus.PENDING);
        if (hasPendingInvitation) {
            return Response.status(422).entity(Map.of("error", "An invitation is already pending for this email")).build();
        }

        // Validate role
        if (request.role == Role.OWNER) {
            return Response.status(422).entity(Map.of("error", "Cannot invite OWNER role")).build();
        }

        // Check tenant plan limits
        long currentUsers = users.stream()
                .filter(u -> u.status != UserStatus.DELETED)
                .count();
        if (tenant.plan.maxUsers != null && currentUsers >= tenant.plan.maxUsers) {
            return Response.status(422).entity(Map.of("error", "Tenant user limit reached")).build();
        }

        // Check if actor has sufficient permissions (ADMIN or OWNER)
        boolean isOwnerOrAdmin = actor.role == Role.OWNER || actor.role == Role.ADMIN;
        if (!isOwnerOrAdmin) {
            return Response.status(403).entity(Map.of("error", "Insufficient permissions")).build();
        }

        // Create invitation
        String invitationId = UUID.randomUUID().toString();
        Instant now = Instant.now();
        Instant expiresAt = now.plus(java.time.Duration.ofDays(7)); // 7 days expiry

        Invitation invitation = new Invitation();
        invitation.id = invitationId;
        invitation.tenantId = tenantId;
        invitation.email = request.email;
        invitation.role = request.role;
        invitation.createdAt = now;
        invitation.expiresAt = expiresAt;
        invitation.resendCount = 0;
        invitation.status = InvitationStatus.PENDING;

        store.invitations.put(invitationId, invitation);

        // Log audit entry
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "INVITATION_CREATED";
        audit.targetId = invitationId;
        audit.timestamp = now;
        audit.details = String.format("Invited %s as %s", request.email, request.role);
        store.auditLog.add(audit);

        // Return success response
        return Response.status(201)
                .entity(Map.of(
                        "id", invitationId,
                        "expiresAt", expiresAt.toString()
                ))
                .build();
    }

    public static class InvitationRequest {
        public String email;
        public Role role;
    }
}
```