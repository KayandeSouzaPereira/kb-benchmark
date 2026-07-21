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

# Task: resend invitation

Implement the invitation resend endpoint:

```
POST /tenants/{tenantId}/invitations/{invitationId}/resend
Success: 200 with JSON { "resendCount": ..., "expiresAt": "..." }
```

Implement ALL the business rules, permissions, validations and error/audit
conventions the team has defined for invitation resends.


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
import java.util.Optional;
import java.util.UUID;

@Path("/tenants/{tenantId}/invitations/{invitationId}/resend")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class InvitationResource {

    @Inject
    InMemoryStore store;

    @POST
    public Response resend(
            @PathParam("tenantId") String tenantId,
            @PathParam("invitationId") String invitationId,
            @HeaderParam("X-Actor-Id") String actorId) {
        
        // Validate inputs
        if (tenantId == null || tenantId.trim().isEmpty()) {
            return Response.status(422).entity("{\"error\":\"Tenant ID is required\"}").build();
        }
        
        if (invitationId == null || invitationId.trim().isEmpty()) {
            return Response.status(422).entity("{\"error\":\"Invitation ID is required\"}").build();
        }
        
        if (actorId == null || actorId.trim().isEmpty()) {
            return Response.status(401).entity("{\"error\":\"Authentication required\"}").build();
        }

        // Find the actor
        Optional<User> actorOpt = store.findUser(actorId);
        if (!actorOpt.isPresent()) {
            return Response.status(401).entity("{\"error\":\"Invalid actor\"}").build();
        }
        User actor = actorOpt.get();

        // Check if actor belongs to the tenant
        if (!tenantId.equals(actor.tenantId)) {
            return Response.status(403).entity("{\"error\":\"Access denied\"}").build();
        }

        // Find the invitation
        Invitation invitation = store.invitations.get(invitationId);
        if (invitation == null) {
            return Response.status(410).entity("{\"error\":\"Invitation not found\"}").build();
        }

        // Check if invitation belongs to the tenant
        if (!tenantId.equals(invitation.tenantId)) {
            return Response.status(403).entity("{\"error\":\"Access denied\"}").build();
        }

        // Check if invitation is already accepted or revoked
        if (InvitationStatus.ACCEPTED.equals(invitation.status) || 
            InvitationStatus.REVOKED.equals(invitation.status)) {
            return Response.status(422).entity("{\"error\":\"Cannot resend an accepted or revoked invitation\"}").build();
        }

        // Check if the actor has permission to resend (owners and admins can resend)
        if (!Role.OWNER.equals(actor.role) && !Role.ADMIN.equals(actor.role)) {
            return Response.status(403).entity("{\"error\":\"Insufficient permissions\"}").build();
        }

        // Check if invitation is expired
        if (Instant.now().isAfter(invitation.expiresAt)) {
            return Response.status(422).entity("{\"error\":\"Cannot resend an expired invitation\"}").build();
        }

        // Check if the invitation has reached max resend limit (10)
        if (invitation.resendCount >= 10) {
            return Response.status(422).entity("{\"error\":\"Maximum resend limit reached\"}").build();
        }

        // Update invitation
        invitation.resendCount++;
        invitation.createdAt = Instant.now();
        invitation.expiresAt = Instant.now().plus(java.time.Duration.ofHours(24));

        // Create audit entry
        AuditEntry auditEntry = new AuditEntry();
        auditEntry.id = UUID.randomUUID().toString();
        auditEntry.tenantId = tenantId;
        auditEntry.actorId = actorId;
        auditEntry.action = "INVITATION_RESEND";
        auditEntry.targetId = invitationId;
        auditEntry.timestamp = Instant.now();
        auditEntry.details = String.format("Invitation resent. New expiration: %s", invitation.expiresAt.toString());
        
        store.auditLog.add(auditEntry);

        // Return response
        return Response.ok()
                .entity(String.format("{\"resendCount\":%d,\"expiresAt\":\"%s\"}", 
                        invitation.resendCount, invitation.expiresAt.toString()))
                .build();
    }
}
```