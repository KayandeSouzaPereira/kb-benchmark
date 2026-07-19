package com.bench.evaltest;

import com.bench.model.Plan;
import com.bench.model.Role;
import com.bench.model.Tenant;
import com.bench.model.User;
import com.bench.model.UserStatus;
import com.bench.store.InMemoryStore;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.time.Instant;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;

@QuarkusTest
public class T2UserDeleteTest {

    @Inject
    InMemoryStore store;

    private void seed() {
        store.reset();
        Tenant t1 = new Tenant();
        t1.id = "t1"; t1.name = "Acme"; t1.plan = Plan.PRO;
        store.tenants.put(t1.id, t1);
        addUser("u-owner", "t1", Role.OWNER);
        addUser("u-admin", "t1", Role.ADMIN);
        addUser("u-member", "t1", Role.MEMBER);
        addUser("u-member2", "t1", Role.MEMBER);
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

    private io.restassured.response.Response delete(String actor, String tenantId, String userId) {
        return given()
                .header("X-Actor-Id", actor)
                .when().delete("/tenants/" + tenantId + "/users/" + userId);
    }

    @Test
    public void adminFazSoftDelete() {
        seed();
        delete("u-admin", "t1", "u-member").then().statusCode(204);
        User u = store.users.get("u-member");
        Assertions.assertNotNull(u, "soft delete: usuario deve continuar no store");
        Assertions.assertEquals(UserStatus.DELETED, u.status);
        Assertions.assertNotNull(u.deletedAt, "deletedAt deve ser preenchido");
    }

    @Test
    public void purgeAtEm30Dias() {
        seed();
        Instant before = Instant.now();
        delete("u-admin", "t1", "u-member").then().statusCode(204);
        Instant after = Instant.now();
        User u = store.users.get("u-member");
        Assertions.assertNotNull(u.purgeAt, "purgeAt deve ser preenchido");
        Instant min = before.plus(Duration.ofDays(30)).minus(Duration.ofMinutes(5));
        Instant max = after.plus(Duration.ofDays(30)).plus(Duration.ofMinutes(5));
        Assertions.assertTrue(!u.purgeAt.isBefore(min) && !u.purgeAt.isAfter(max),
                "purgeAt deve ser ~30 dias no futuro, foi: " + u.purgeAt);
    }

    @Test
    public void auditoriaRegistraSoftDelete() {
        seed();
        delete("u-admin", "t1", "u-member2").then().statusCode(204);
        boolean found = store.auditLog.stream().anyMatch(a ->
                "USER_SOFT_DELETED".equals(a.action)
                        && "u-admin".equals(a.actorId)
                        && "u-member2".equals(a.targetId));
        Assertions.assertTrue(found, "audit log deve conter USER_SOFT_DELETED com target u-member2");
    }

    @Test
    public void memberNaoPodeDeletar() {
        seed();
        delete("u-member", "t1", "u-member2")
                .then().statusCode(403).body("code", equalTo("FORBIDDEN_ROLE"));
        Assertions.assertEquals(UserStatus.ACTIVE, store.users.get("u-member2").status);
    }

    @Test
    public void adminNaoPodeDeletarOwner() {
        seed();
        delete("u-admin", "t1", "u-owner")
                .then().statusCode(403).body("code", equalTo("OWNER_PROTECTED"));
        Assertions.assertEquals(UserStatus.ACTIVE, store.users.get("u-owner").status);
    }

    @Test
    public void ninguemDeletaASiMesmo() {
        seed();
        delete("u-admin", "t1", "u-admin")
                .then().statusCode(422).body("code", equalTo("CANNOT_DELETE_SELF"));
        Assertions.assertEquals(UserStatus.ACTIVE, store.users.get("u-admin").status);
    }

    @Test
    public void atorDeOutroTenantRecebe404() {
        seed();
        delete("u-x", "t1", "u-member").then().statusCode(404);
        Assertions.assertEquals(UserStatus.ACTIVE, store.users.get("u-member").status);
    }
}
