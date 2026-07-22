package com.bench.model;

public class Tenant {
    public String id;
    public String name;
    public Plan plan;
    /** default is IMMEDIATE when not explicitly set by a test */
    public NotificationDigestMode notificationDigestMode = NotificationDigestMode.IMMEDIATE;
}
