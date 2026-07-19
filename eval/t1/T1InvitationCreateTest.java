package com.bench.evaltest;

import com.bench.model.Invitation;
import com.bench.model.InvitationStatus;
import com.bench.model.Plan;
import com.bench.model.Role;
import com.bench.model.Tenant;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.store.InMemoryStore;
import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.time.Instant;
import java.util.List;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;

@QuarkusTest
public class T1InvitationCreateTest {

    @Inject
    InMemoryStore store;

    private void seed() {
        store.reset();
        Tenant t1 = new Tenant();
        t1.id = "t1"; t1.name = "Acme"; t1.plan = Plan.FREE;
        store.tenants.put(t1.id, t1);
        addUser("u-owner", "t1", Role.OWNER);
        addUser("u-admin", "t1", Role.ADMIN);
        addUser("u-member", "t1", Role.MEMBER);
        Tenant t2 = new Tenant();
        t2.id = "t2"; t2.name = "Outra"; t2.plan = Plan.PRO;
        store.tenants.put(t2.id, t2);
        addUser("u-x", "t2", Role.ADMIN);
    }

    private void addUser(String id, String tenantId, Role role) {
        User u = new User();
        u.id = id; u.tenantId = tenantId; u.email = id + "@ex.com";
        u.role = role; u.status = UserStatus.ACTIVE;
        store.users.put(id, u);
    }

    private void addPendingInvitation(String id, String tenantId) {
        Invitation i = new Invitation();
        i.id = id; i.tenantId = tenantId; i.email = id + "@ex.com"; i.role = Role.MEMBER;
        i.createdAt = Instant.now();
        i.expiresAt = Instant.now().plus(Duration.ofHours(72));
        i.resendCount = 0;
        i.status = InvitationStatus.PENDING;
        store.invitations.put(id, i);
    }

    private io.restassured.response.Response post(String actor, String tenantId, String email) {
        return given()
                .contentType(ContentType.JSON)
                .header("X-Actor-Id", actor)
                .body("{\"email\":\"" + email + "\",\"role\":\"MEMBER\"}")
                .when().post("/tenants/" + tenantId + "/invitations");
    }

    @Test
    public void adminCriaConvitePersistido() {
        seed();
        post("u-admin", "t1", "novo@ex.com").then().statusCode(201);
        List<Invitation> invs = store.invitationsOfTenant("t1").stream()
                .filter(i -> "novo@ex.com".equals(i.email)).toList();
        Assertions.assertEquals(1, invs.size(), "convite deve ser persistido no store");
        Assertions.assertEquals(InvitationStatus.PENDING, invs.get(0).status);
    }

    @Test
    public void conviteExpiraEm72Horas() {
        seed();
        Instant before = Instant.now();
        post("u-admin", "t1", "novo72@ex.com").then().statusCode(201);
        Instant after = Instant.now();
        Invitation inv = store.invitationsOfTenant("t1").stream()
                .filter(i -> "novo72@ex.com".equals(i.email)).findFirst().orElseThrow();
        Assertions.assertNotNull(inv.expiresAt, "expiresAt deve ser definido");
        Instant min = before.plus(Duration.ofHours(72)).minus(Duration.ofMinutes(5));
        Instant max = after.plus(Duration.ofHours(72)).plus(Duration.ofMinutes(5));
        Assertions.assertTrue(!inv.expiresAt.isBefore(min) && !inv.expiresAt.isAfter(max),
                "expiresAt deve ser ~72h no futuro, foi: " + inv.expiresAt);
    }

    @Test
    public void auditoriaRegistraUserInvited() {
        seed();
        post("u-admin", "t1", "audit@ex.com").then().statusCode(201);
        boolean found = store.auditLog.stream().anyMatch(a ->
                "USER_INVITED".equals(a.action)
                        && "u-admin".equals(a.actorId)
                        && "t1".equals(a.tenantId));
        Assertions.assertTrue(found, "audit log deve conter USER_INVITED do ator u-admin");
    }

    @Test
    public void memberNaoPodeConvidar() {
        seed();
        post("u-member", "t1", "barrado@ex.com")
                .then().statusCode(403).body("code", equalTo("FORBIDDEN_ROLE"));
        Assertions.assertTrue(store.invitationsOfTenant("t1").isEmpty(),
                "nenhum convite deve ser criado");
    }

    @Test
    public void limiteDoPlanoFreeContaConvitesPendentes() {
        seed(); // 3 usuarios ativos no t1 (FREE = 5)
        addPendingInvitation("i1", "t1");
        addPendingInvitation("i2", "t1"); // 3 usuarios + 2 pendentes = 5 (limite atingido)
        post("u-admin", "t1", "estourou@ex.com")
                .then().statusCode(422).body("code", equalTo("PLAN_LIMIT_EXCEEDED"));
        Assertions.assertEquals(2, store.invitationsOfTenant("t1").size(),
                "nenhum convite novo deve ser criado");
    }

    @Test
    public void atorDeOutroTenantRecebe404() {
        seed();
        post("u-x", "t1", "intruso@ex.com").then().statusCode(404);
        Assertions.assertTrue(store.invitationsOfTenant("t1").isEmpty());
    }
}
