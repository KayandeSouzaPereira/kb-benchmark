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
        
        // Validate request
        if (request == null || request.role == null) {
            return Response.status(422)
                    .entity("Role is required")
                    .build();
        }

        // Find the actor user
        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(401)
                    .entity("Unauthorized")
                    .build();
        }
        User actor = actorOpt.get();

        // Verify actor is in the same tenant
        if (!tenantId.equals(actor.tenantId)) {
            return Response.status(403)
                    .entity("Forbidden")
                    .build();
        }

        // Find the target user
        Optional<User> targetUserOpt = store.findUser(userId);
        if (!targetUserOpt.isPresent()) {
            return Response.status(404)
                    .entity("User not found")
                    .build();
        }
        User targetUser = targetUserOpt.get();

        // Verify target user is in the same tenant
        if (!tenantId.equals(targetUser.tenantId)) {
            return Response.status(404)
                    .entity("User not found")
                    .build();
        }

        // Check if actor has permission to change role (OWNER or ADMIN)
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return Response.status(403)
                    .entity("Forbidden")
                    .build();
        }

        // Cannot change role of a deleted user
        if (targetUser.status == UserStatus.DELETED) {
            return Response.status(410)
                    .entity("User is deleted")
                    .build();
        }

        // Cannot change role of the actor themselves
        if (actorId.equals(userId)) {
            return Response.status(422)
                    .entity("Cannot change your own role")
                    .build();
        }

        // Validate that we're not removing the last OWNER
        if (targetUser.role == Role.OWNER && request.role != Role.OWNER) {
            long ownerCount = store.countOwners(tenantId);
            if (ownerCount <= 1) {
                return Response.status(422)
                        .entity("Cannot remove the last OWNER")
                        .build();
            }
        }

        // Validate role change is allowed
        if (!isValidRoleChange(actor.role, targetUser.role, request.role)) {
            return Response.status(422)
                    .entity("Invalid role change")
                    .build();
        }

        // Update user role
        targetUser.role = request.role;

        // Create audit entry
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "USER_ROLE_CHANGED";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = String.format("Changed role from %s to %s", targetUser.role, request.role);
        store.auditLog.add(auditEntry);

        return Response.ok(targetUser).build();
    }

    private boolean isValidRoleChange(Role actorRole, Role currentRole, Role newRole) {
        // OWNER can change any role
        if (actorRole == Role.OWNER) {
            return true;
        }
        
        // ADMIN can only change MEMBER to ADMIN or MEMBER, and cannot change other admins
        if (actorRole == Role.ADMIN) {
            // ADMIN cannot change another ADMIN's role
            if (currentRole == Role.ADMIN && newRole != Role.ADMIN) {
                return false;
            }
            
            // ADMIN can only promote members to admin
            if (currentRole == Role.MEMBER && newRole == Role.ADMIN) {
                return true;
            }
            
            // ADMIN cannot demote members or change roles of other admins
            return false;
        }
        
        return false;
    }

    public static class ChangeRoleRequest {
        public Role role;
    }
}
```