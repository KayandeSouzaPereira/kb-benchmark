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

# Implementation Plan

I'll create a user invitation endpoint that follows all the business rules and conventions. Here's my approach:

1. Create a REST resource class for handling invitations
2. Implement validation for:
   - Tenant existence
   - Actor permissions (must be ADMIN or OWNER)
   - Email format and uniqueness
   - Role validation
   - Invitation limits based on tenant plan
3. Implement business logic for:
   - Creating invitations
   - Checking user already exists
   - Audit logging
4. Handle all error cases with appropriate HTTP status codes

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
        // Validate tenant exists
        Optional<Tenant> tenantOpt = store.tenants.values().stream()
                .filter(t -> t.id.equals(tenantId))
                .findFirst();
        
        if (tenantOpt.isEmpty()) {
            return Response.status(404).entity("Tenant not found").build();
        }
        
        Tenant tenant = tenantOpt.get();
        
        // Validate actor exists and has proper permissions
        Optional<User> actorOpt = store.findUser(actorId);
        if (actorOpt.isEmpty()) {
            return Response.status(401).entity("Unauthorized").build();
        }
        
        User actor = actorOpt.get();
        if (!actor.tenantId.equals(tenantId)) {
            return Response.status(403).entity("Forbidden").build();
        }
        
        if (actor.status != UserStatus.ACTIVE) {
            return Response.status(403).entity("Forbidden").build();
        }
        
        // Check if actor has permission to invite (ADMIN or OWNER)
        if (actor.role != Role.ADMIN && actor.role != Role.OWNER) {
            return Response.status(403).entity("Forbidden").build();
        }
        
        // Validate email
        if (request.email == null || request.email.isEmpty()) {
            return Response.status(422).entity("Email is required").build();
        }
        
        if (!isValidEmail(request.email)) {
            return Response.status(422).entity("Invalid email format").build();
        }
        
        // Check if user with this email already exists in the tenant
        List<User> existingUsers = store.usersOfTenant(tenantId);
        if (existingUsers.stream().anyMatch(u -> u.email.equals(request.email))) {
            return Response.status(422).entity("User with this email already exists").build();
        }
        
        // Check if user has already been invited to this tenant
        List<Invitation> existingInvitations = store.invitationsOfTenant(tenantId);
        if (existingInvitations.stream().anyMatch(i -> i.email.equals(request.email) && i.status == InvitationStatus.PENDING)) {
            return Response.status(422).entity("User has already been invited").build();
        }
        
        // Validate role
        if (request.role == null) {
            return Response.status(422).entity("Role is required").build();
        }
        
        // Check if tenant plan allows for more users
        if (tenant.plan.maxUsers != null) {
            long totalUsers = existingUsers.stream()
                    .filter(u -> u.status != UserStatus.DELETED)
                    .count();
            
            long totalInvitations = existingInvitations.stream()
                    .filter(i -> i.status == InvitationStatus.PENDING)
                    .count();
            
            if (totalUsers + totalInvitations >= tenant.plan.maxUsers) {
                return Response.status(422).entity("Tenant plan limit reached").build();
            }
        }
        
        // Check if we're trying to invite an OWNER role
        if (request.role == Role.OWNER) {
            // Only allow if there's currently no OWNER in the tenant
            long ownersCount = store.countOwners(tenantId);
            if (ownersCount > 0) {
                return Response.status(422).entity("Tenant already has an owner").build();
            }
        }
        
        // Create invitation
        Invitation invitation = new Invitation();
        invitation.id = UUID.randomUUID().toString();
        invitation.tenantId = tenantId;
        invitation.email = request.email;
        invitation.role = request.role;
        invitation.createdAt = Instant.now();
        invitation.expiresAt = Instant.now().plus(java.time.Duration.ofDays(7));
        invitation.resendCount = 0;
        invitation.status = InvitationStatus.PENDING;
        
        // Store invitation
        store.invitations.put(invitation.id, invitation);
        
        // Log audit entry
        AuditEntry audit = new AuditEntry();
        audit.id = UUID.randomUUID().toString();
        audit.tenantId = tenantId;
        audit.actorId = actorId;
        audit.action = "INVITE_USER";
        audit.targetId = invitation.id;
        audit.timestamp = Instant.now();
        audit.details = String.format("Invited %s with role %s", invitation.email, invitation.role);
        
        store.auditLog.add(audit);
        
        // Return success response
        InvitationResponse response = new InvitationResponse();
        response.id = invitation.id;
        response.expiresAt = invitation.expiresAt;
        
        return Response.status(201).entity(response).build();
    }
    
    private boolean isValidEmail(String email) {
        if (email == null || email.isEmpty()) {
            return false;
        }
        return email.matches("^[A-Za-z0-9+_.-]+@([A-Za-z0-9.-]+\\.[A-Za-z]{2,})$");
    }
    
    public static class InvitationRequest {
        public String email;
        public Role role;
    }
    
    public static class InvitationResponse {
        public String id;
        public Instant expiresAt;
    }
}
```