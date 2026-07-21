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

```java
FILE: src/main/java/com/bench/api/UserResource.java
```java
package com.bench.api;

import com.bench.model.*;
import com.bench.store.InMemoryStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.Response;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Path("/tenants/{tenantId}/users/{userId}")
public class UserResource {

    @Inject
    InMemoryStore store;

    @DELETE
    public Response deleteUser(
            @PathParam("tenantId") String tenantId,
            @PathParam("userId") String userId,
            @HeaderParam("X-Actor-Id") String actorId) {
        
        // Validate tenant ID
        if (tenantId == null || tenantId.trim().isEmpty()) {
            return Response.status(422).entity("Tenant ID is required").build();
        }

        // Validate user ID
        if (userId == null || userId.trim().isEmpty()) {
            return Response.status(422).entity("User ID is required").build();
        }

        // Validate actor ID
        if (actorId == null || actorId.trim().isEmpty()) {
            return Response.status(401).entity("Authentication required").build();
        }

        // Find the actor user
        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(401).entity("Invalid actor ID").build();
        }
        User actor = actorOpt.get();

        // Check if actor belongs to the same tenant
        if (!tenantId.equals(actor.tenantId)) {
            return Response.status(403).entity("Access denied").build();
        }

        // Find the user to be deleted
        Optional<User> userToDeleteOpt = store.findUser(userId);
        if (!userToDeleteOpt.isPresent()) {
            return Response.status(404).entity("User not found").build();
        }
        User userToDelete = userToDeleteOpt.get();

        // Check if user belongs to the same tenant
        if (!tenantId.equals(userToDelete.tenantId)) {
            return Response.status(404).entity("User not found in tenant").build();
        }

        // Check if user is already deleted
        if (UserStatus.DELETED.equals(userToDelete.status)) {
            return Response.status(410).entity("User already deleted").build();
        }

        // Check if actor is trying to delete themselves
        if (actorId.equals(userId)) {
            return Response.status(422).entity("Cannot delete yourself").build();
        }

        // Check permissions - only OWNER or ADMIN can delete users
        if (Role.MEMBER.equals(actor.role)) {
            return Response.status(403).entity("Insufficient permissions").build();
        }

        // Check if user to delete is an OWNER and there's only one OWNER left
        if (Role.OWNER.equals(userToDelete.role) && store.countOwners(tenantId) <= 1) {
            return Response.status(422).entity("Cannot remove the last owner").build();
        }

        // Check tenant plan limits - if user is not an OWNER, we can delete
        // But we need to ensure that deleting this user won't violate plan limits
        Tenant tenant = store.tenants.get(tenantId);
        if (tenant != null && tenant.plan.maxUsers != null) {
            List<User> activeUsers = store.usersOfTenant(tenantId)
                    .stream()
                    .filter(u -> !UserStatus.DELETED.equals(u.status))
                    .filter(u -> Role.OWNER.equals(u.role) || Role.ADMIN.equals(u.role))
                    .toList();
            
            if (activeUsers.size() > tenant.plan.maxUsers) {
                return Response.status(422).entity("Tenant plan limit exceeded").build();
            }
        }

        // Perform deletion
        userToDelete.status = UserStatus.DELETED;
        userToDelete.deletedAt = Instant.now();
        
        // Set purge time (30 days from now)
        userToDelete.purgeAt = Instant.now().plus(java.time.Duration.ofDays(30));

        // Create audit entry
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = java.util.UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "USER_DELETE";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = String.format("User %s deleted by %s", userId, actorId);
        
        store.auditLog.add(auditEntry);

        return Response.noContent().build();
    }
}
```