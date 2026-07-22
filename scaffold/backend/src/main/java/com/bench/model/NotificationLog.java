package com.bench.model;

import java.time.Instant;

public class NotificationLog {
    public String id;
    public String tenantId;
    public String templateId;
    public NotificationStatus status;
    public Instant createdAt;
}
