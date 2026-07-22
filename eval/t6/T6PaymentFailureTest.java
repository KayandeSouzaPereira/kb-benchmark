package com.bench.evaltest;

import com.bench.model.NotificationDigestMode;
import com.bench.model.NotificationLog;
import com.bench.model.NotificationStatus;
import com.bench.model.Plan;
import com.bench.model.Tenant;
import com.bench.model.WebhookConfig;
import com.bench.model.WebhookDelivery;
import com.bench.model.WebhookDeliveryStatus;
import com.bench.store.InMemoryStore;
import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.time.Instant;
import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;

import static io.restassured.RestAssured.given;

@QuarkusTest
public class T6PaymentFailureTest {

    @Inject
    InMemoryStore store;

    private static final Pattern HEX64 = Pattern.compile("^[0-9a-f]{64}$");

    private void seed() {
        store.reset();
        Tenant t = new Tenant();
        t.id = "t1";
        t.name = "Acme";
        t.plan = Plan.PRO;
        store.tenants.put(t.id, t);

        WebhookConfig cfg = new WebhookConfig();
        cfg.tenantId = "t1";
        cfg.url = "https://acme.example.com/hooks";
        cfg.secret = "whsec_test_123456";
        store.webhookConfigs.put("t1", cfg);
    }

    private void seedRecentDeliveries(int count, Instant createdAt) {
        for (int i = 0; i < count; i++) {
            WebhookDelivery d = new WebhookDelivery();
            d.id = "pre-" + i;
            d.tenantId = "t1";
            d.eventType = "user.invited";
            d.signature = "0".repeat(64);
            d.status = WebhookDeliveryStatus.DELIVERED;
            d.attemptCount = 1;
            d.maxAttempts = 5;
            d.createdAt = createdAt;
            store.webhookDeliveries.put(d.id, d);
        }
    }

    private WebhookDelivery postAndGetNewDelivery(String invoiceId, int amountCents) {
        Set<String> before = new HashSet<>(store.webhookDeliveries.keySet());
        given()
                .contentType(ContentType.JSON)
                .body("{\"invoiceId\":\"" + invoiceId + "\",\"amountCents\":" + amountCents + "}")
                .when().post("/tenants/t1/billing/payment-failures")
                .then().statusCode(201);
        Set<String> after = new HashSet<>(store.webhookDeliveries.keySet());
        after.removeAll(before);
        Assertions.assertEquals(1, after.size(),
                "exactly one new WebhookDelivery should be created, found: " + after.size());
        return store.webhookDeliveries.get(after.iterator().next());
    }

    private NotificationLog latestNotification(Set<String> before) {
        Set<String> after = new HashSet<>(store.notificationLogs.keySet());
        after.removeAll(before);
        Assertions.assertEquals(1, after.size(),
                "exactly one new NotificationLog should be created, found: " + after.size());
        return store.notificationLogs.get(after.iterator().next());
    }

    @Test
    public void createsSignedWebhookDelivery() {
        seed();
        WebhookDelivery d = postAndGetNewDelivery("inv_1", 4900);
        Assertions.assertEquals("t1", d.tenantId);
        Assertions.assertEquals("payment.failed", d.eventType);
        Assertions.assertNotNull(d.signature, "signature must be set");
        Assertions.assertTrue(HEX64.matcher(d.signature).matches(),
                "signature must be a 64-char lowercase hex string (HMAC-SHA256), was: " + d.signature);
    }

    @Test
    public void setsMaxAttemptsAndPendingStatusWhenUnderLimit() {
        seed();
        WebhookDelivery d = postAndGetNewDelivery("inv_2", 4900);
        Assertions.assertEquals(5, d.maxAttempts, "maxAttempts must follow the team's retry policy");
        Assertions.assertEquals(0, d.attemptCount);
        Assertions.assertEquals(WebhookDeliveryStatus.PENDING, d.status);
    }

    @Test
    public void deferredWhenTenantOverRateLimit() {
        seed();
        seedRecentDeliveries(10, Instant.now().minus(Duration.ofMinutes(5)));
        WebhookDelivery d = postAndGetNewDelivery("inv_3", 4900);
        Assertions.assertEquals(WebhookDeliveryStatus.DEFERRED, d.status,
                "tenant already has 10 deliveries in the last 60 minutes; new one must be DEFERRED");
    }

    @Test
    public void notImpactedByDeliveriesOutsideRollingWindow() {
        seed();
        seedRecentDeliveries(10, Instant.now().minus(Duration.ofMinutes(90)));
        WebhookDelivery d = postAndGetNewDelivery("inv_4", 4900);
        Assertions.assertEquals(WebhookDeliveryStatus.PENDING, d.status,
                "the 10 prior deliveries are outside the 60-minute rolling window and must not count");
    }

    @Test
    public void sendsImmediateNotificationWithCorrectTemplateByDefault() {
        seed();
        Set<String> before = new HashSet<>(store.notificationLogs.keySet());
        postAndGetNewDelivery("inv_5", 4900);
        NotificationLog n = latestNotification(before);
        Assertions.assertEquals("t1", n.tenantId);
        Assertions.assertEquals("payment_failed_v2", n.templateId,
                "must use the current template id, not the retired one");
        Assertions.assertEquals(NotificationStatus.SENT, n.status,
                "tenant's digest mode defaults to IMMEDIATE, so the notification must be SENT right away");
    }

    @Test
    public void queuesNotificationWhenTenantPrefersDailyDigest() {
        seed();
        store.tenants.get("t1").notificationDigestMode = NotificationDigestMode.DAILY_DIGEST;
        Set<String> before = new HashSet<>(store.notificationLogs.keySet());
        postAndGetNewDelivery("inv_6", 4900);
        NotificationLog n = latestNotification(before);
        Assertions.assertEquals("payment_failed_v2", n.templateId);
        Assertions.assertEquals(NotificationStatus.QUEUED, n.status,
                "tenant prefers DAILY_DIGEST, so the notification must be QUEUED, not sent immediately");
    }
}
