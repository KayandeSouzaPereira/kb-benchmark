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
        
        // Validate tenant and user exist
        Optional<User> targetUserOpt = store.findUser(userId);
        if (targetUserOpt.isEmpty()) {
            return Response.status(404).build();
        }
        
        User targetUser = targetUserOpt.get();
        if (!tenantId.equals(targetUser.tenantId)) {
            return Response.status(404).build();
        }
        
        // Validate actor exists
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(401).build();
        }
        
        User actor = actorOpt.get();
        if (!tenantId.equals(actor.tenantId)) {
            return Response.status(401).build();
        }
        
        // Check permissions
        if (actor.status == UserStatus.DELETED) {
            return Response.status(401).build();
        }
        
        // Cannot delete self
        if (userId.equals(actorId)) {
            return Response.status(400).entity("Cannot delete yourself").build();
        }
        
        // Check if actor has permission to delete (OWNER or ADMIN)
        if (actor.role != Role.OWNER && actor.role != Role.ADMIN) {
            return Response.status(403).build();
        }
        
        // Cannot delete users from other tenants
        if (!targetUser.tenantId.equals(tenantId)) {
            return Response.status(403).build();
        }
        
        // Check if user is already deleted
        if (targetUser.status == UserStatus.DELETED) {
            return Response.status(204).build();
        }
        
        // Cannot delete the last owner
        if (targetUser.role == Role.OWNER && store.countOwners(tenantId) <= 1) {
            return Response.status(422).entity("Cannot delete the last owner").build();
        }
        
        // Perform deletion
        targetUser.status = UserStatus.DELETED;
        targetUser.deletedAt = Instant.now();
        
        // Set purge time (30 days from now)
        targetUser.purgeAt = Instant.now().plus(java.time.Duration.ofDays(30));
        
        // Create audit entry
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = java.util.UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "USER_DELETED";
        auditEntry.targetId = userId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = "User deleted by " + actor.email;
        
        store.auditLog.add(auditEntry);
        
        return Response.noContent().build();
    }
}
```