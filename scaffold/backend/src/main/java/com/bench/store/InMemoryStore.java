package com.bench.store;

import com.bench.model.Invitation;
import com.bench.model.AuditEntry;
import com.bench.model.NotificationLog;
import com.bench.model.Role;
import com.bench.model.Tenant;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.model.WebhookConfig;
import com.bench.model.WebhookDelivery;
import jakarta.inject.Singleton;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

// @Singleton (sem client proxy): campos publicos e metodos enxergam a MESMA
// instancia — com @ApplicationScoped o proxy separa acesso a campo de chamada
// de metodo e o store "se divide" em dois.
@Singleton
public class InMemoryStore {

    public final Map<String, Tenant> tenants = new ConcurrentHashMap<>();
    public final Map<String, User> users = new ConcurrentHashMap<>();
    public final Map<String, Invitation> invitations = new ConcurrentHashMap<>();
    public final List<AuditEntry> auditLog = Collections.synchronizedList(new ArrayList<>());
    public final Map<String, WebhookConfig> webhookConfigs = new ConcurrentHashMap<>();
    public final Map<String, WebhookDelivery> webhookDeliveries = new ConcurrentHashMap<>();
    public final Map<String, NotificationLog> notificationLogs = new ConcurrentHashMap<>();

    public void reset() {
        tenants.clear();
        users.clear();
        invitations.clear();
        auditLog.clear();
        webhookConfigs.clear();
        webhookDeliveries.clear();
        notificationLogs.clear();
    }

    public Optional<User> findUser(String id) {
        return Optional.ofNullable(users.get(id));
    }

    public List<User> usersOfTenant(String tenantId) {
        return users.values().stream()
                .filter(u -> tenantId.equals(u.tenantId))
                .toList();
    }

    public List<Invitation> invitationsOfTenant(String tenantId) {
        return invitations.values().stream()
                .filter(i -> tenantId.equals(i.tenantId))
                .toList();
    }

    public long countOwners(String tenantId) {
        return usersOfTenant(tenantId).stream()
                .filter(u -> u.role == Role.OWNER && u.status != UserStatus.DELETED)
                .count();
    }

    public long countRecentWebhookDeliveries(String tenantId, Instant since) {
        return webhookDeliveries.values().stream()
                .filter(d -> tenantId.equals(d.tenantId) && d.createdAt.isAfter(since))
                .count();
    }
}
