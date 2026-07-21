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
            return Response.status(422).entity("Role is required").build();
        }

        // Find the actor user
        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(401).entity("Unauthorized").build();
        }
        User actor = actorOpt.get();

        // Verify actor belongs to the same tenant
        if (!tenantId.equals(actor.tenantId)) {
            return Response.status(403).entity("Forbidden").build();
        }

        // Find the target user
        Optional<User> targetUserOpt = store.findUser(userId);
        if (!targetUserOpt.isPresent()) {
            return Response.status(404).entity("User not found").build();
        }
        User targetUser = targetUserOpt.get();

        // Verify target user belongs to the same tenant
        if (!tenantId.equals(targetUser.tenantId)) {
            return Response.status(403).entity("Forbidden").build();
        }

        // Check if actor has permission to change roles (OWNER or ADMIN)
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return Response.status(403).entity("Insufficient permissions").build();
        }

        // Check if target user is deleted
        if (targetUser.status == UserStatus.DELETED) {
            return Response.status(410).entity("User has been deleted").build();
        }

        // Validate role change is allowed
        if (!isRoleChangeAllowed(actor, targetUser, request.role)) {
            return Response.status(422).entity("Invalid role change").build();
        }

        // Perform the role change
        Role oldRole = targetUser.role;
        targetUser.role = request.role;

        // Create audit entry
        createAuditEntry(tenantId, actorId, userId, "ROLE_CHANGED", 
                        String.format("Changed role from %s to %s", oldRole, request.role));

        return Response.ok(targetUser).build();
    }

    private boolean isRoleChangeAllowed(User actor, User targetUser, Role newRole) {
        // OWNER can change to any role
        if (actor.role == Role.OWNER) {
            return true;
        }
        
        // ADMIN can only change to MEMBER or ADMIN (not OWNER)
        if (actor.role == Role.ADMIN) {
            if (newRole == Role.OWNER) {
                return false; // ADMIN cannot promote to OWNER
            }
            // ADMIN can demote to MEMBER or promote to ADMIN (if target is MEMBER)
            return true;
        }
        
        return false;
    }

    private void createAuditEntry(String tenantId, String actorId, String targetId, 
                                 String action, String details) {
        AuditEntry entry = new AuditEntry();
        entry.id = UUID.randomUUID().toString();
        entry.tenantId = tenantId;
        entry.actorId = actorId;
        entry.targetId = targetId;
        entry.action = action;
        entry.timestamp = Instant.now();
        entry.details = details;
        store.auditLog.add(entry);
    }

    public static class ChangeRoleRequest {
        public Role role;
    }
}
```