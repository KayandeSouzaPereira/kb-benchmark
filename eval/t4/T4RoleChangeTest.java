package com.bench.evaltest;

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

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;

@QuarkusTest
public class T4RoleChangeTest {

    @Inject
    InMemoryStore store;

    private void seed(int owners) {
        store.reset();
        Tenant t1 = new Tenant();
        t1.id = "t1"; t1.name = "Acme"; t1.plan = Plan.PRO;
        store.tenants.put(t1.id, t1);
        addUser("u-owner1", "t1", Role.OWNER);
        if (owners > 1) {
            addUser("u-owner2", "t1", Role.OWNER);
        }
        addUser("u-admin", "t1", Role.ADMIN);
        addUser("u-member", "t1", Role.MEMBER);
    }

    private void addUser(String id, String tenantId, Role role) {
        User u = new User();
        u.id = id; u.tenantId = tenantId; u.email = id + "@ex.com";
        u.role = role; u.status = UserStatus.ACTIVE;
        store.users.put(id, u);
    }

    private io.restassured.response.Response patchRole(String actor, String userId, String role) {
        return given()
                .contentType(ContentType.JSON)
                .header("X-Actor-Id", actor)
                .body("{\"role\":\"" + role + "\"}")
                .when().patch("/tenants/t1/users/" + userId + "/role");
    }

    @Test
    public void adminPromoveMember() {
        seed(1);
        patchRole("u-admin", "u-member", "ADMIN").then().statusCode(200);
        Assertions.assertEquals(Role.ADMIN, store.users.get("u-member").role);
    }

    @Test
    public void auditoriaRegistraMudancaDePapel() {
        seed(1);
        patchRole("u-admin", "u-member", "ADMIN").then().statusCode(200);
        boolean found = store.auditLog.stream().anyMatch(a ->
                "USER_ROLE_CHANGED".equals(a.action)
                        && "u-admin".equals(a.actorId)
                        && "u-member".equals(a.targetId));
        Assertions.assertTrue(found, "audit log deve conter USER_ROLE_CHANGED com target u-member");
    }

    @Test
    public void adminNaoAlteraPapelDeOwner() {
        seed(1);
        patchRole("u-admin", "u-owner1", "MEMBER")
                .then().statusCode(403).body("code", equalTo("OWNER_PROTECTED"));
        Assertions.assertEquals(Role.OWNER, store.users.get("u-owner1").role);
    }

    @Test
    public void ownerPodeRebaixarOutroOwner() {
        seed(2);
        patchRole("u-owner1", "u-owner2", "ADMIN").then().statusCode(200);
        Assertions.assertEquals(Role.ADMIN, store.users.get("u-owner2").role);
    }

    @Test
    public void ultimoOwnerNaoPodeSerRebaixado() {
        seed(1);
        patchRole("u-owner1", "u-owner1", "ADMIN")
                .then().statusCode(409).body("code", equalTo("LAST_OWNER"));
        Assertions.assertEquals(Role.OWNER, store.users.get("u-owner1").role);
    }

    @Test
    public void memberNaoAlteraPapeis() {
        seed(1);
        patchRole("u-member", "u-admin", "MEMBER")
                .then().statusCode(403).body("code", equalTo("FORBIDDEN_ROLE"));
        Assertions.assertEquals(Role.ADMIN, store.users.get("u-admin").role);
    }
}
