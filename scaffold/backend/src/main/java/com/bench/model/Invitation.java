package com.bench.model;

import java.time.Instant;

public class Invitation {
    public String id;
    public String tenantId;
    public String email;
    public Role role;
    public Instant createdAt;
    public Instant expiresAt;
    public int resendCount;
    public InvitationStatus status;
}
