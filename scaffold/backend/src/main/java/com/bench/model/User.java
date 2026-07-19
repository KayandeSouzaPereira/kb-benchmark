package com.bench.model;

import java.time.Instant;

public class User {
    public String id;
    public String tenantId;
    public String email;
    public Role role;
    public UserStatus status;
    public Instant deletedAt;
    public Instant purgeAt;
}
