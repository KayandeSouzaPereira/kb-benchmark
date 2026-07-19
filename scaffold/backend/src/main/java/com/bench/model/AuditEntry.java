package com.bench.model;

import java.time.Instant;

public class AuditEntry {
    public String id;
    public String tenantId;
    public String actorId;
    public String action;
    public String targetId;
    public Instant timestamp;
    public String details;
}
