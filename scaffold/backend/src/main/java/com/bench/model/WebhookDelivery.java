package com.bench.model;

import java.time.Instant;

public class WebhookDelivery {
    public String id;
    public String tenantId;
    public String eventType;
    public String signature;
    public WebhookDeliveryStatus status;
    public int attemptCount;
    public int maxAttempts;
    public Instant createdAt;
}
