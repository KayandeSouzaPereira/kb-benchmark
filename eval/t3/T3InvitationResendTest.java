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
import jakarta.inject.Inject;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.time.Instant;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;

@QuarkusTest
public class T3InvitationResendTest {

    @Inject
    InMemoryStore store;

    private void seed() {
        store.reset();
        Tenant t1 = new Tenant();
        t1.id = "t1"; t1.name = "Acme"; t1.plan = Plan.PRO;
        store.tenants.put(t1.id, t1);
        addUser("u-admin", "t1", Role.ADMIN);
        addUser("u-member", "t1", Role.MEMBER);
        addInvitation("inv-ok", 0, Instant.now().plus(Duration.ofHours(24)));
        addInvitation("inv-expirado", 0, Instant.now().minus(Duration.ofHours(1)));
        addInvitation("inv-esgotado", 3, Instant.now().plus(Duration.ofHours(24)));
    }

    private void addUser(String id, String tenantId, Role role) {
        User u = new User();
        u.id = id; u.tenantId = tenantId; u.email = id + "@ex.com";
        u.role = role; u.status = UserStatus.ACTIVE;
        store.users.put(id, u);
    }

    private void addInvitation(String id, int resendCount, Instant expiresAt) {
        Invitation i = new Invitation();
        i.id = id; i.tenantId = "t1"; i.email = id + "@ex.com"; i.role = Role.MEMBER;
        i.createdAt = Instant.now().minus(Duration.ofHours(48));
        i.expiresAt = expiresAt;
        i.resendCount = resendCount;
        i.status = InvitationStatus.PENDING;
        store.invitations.put(id, i);
    }

    private io.restassured.response.Response resend(String actor, String invitationId) {
        return given()
                .header("X-Actor-Id", actor)
                .when().post("/tenants/t1/invitations/" + invitationId + "/resend");
    }

    @Test
    public void reenvioIncrementaContadorEResetaExpiracao() {
        seed();
        Instant before = Instant.now();
        resend("u-admin", "inv-ok").then().statusCode(200);
        Instant after = Instant.now();
        Invitation inv = store.invitations.get("inv-ok");
        Assertions.assertEquals(1, inv.resendCount, "resendCount deve ir a 1");
        Instant min = before.plus(Duration.ofHours(72)).minus(Duration.ofMinutes(5));
        Instant max = after.plus(Duration.ofHours(72)).plus(Duration.ofMinutes(5));
        Assertions.assertTrue(!inv.expiresAt.isBefore(min) && !inv.expiresAt.isAfter(max),
                "expiracao deve ser resetada para ~72h no futuro, foi: " + inv.expiresAt);
    }

    @Test
    public void reenvioReativaConviteExpirado() {
        seed();
        resend("u-admin", "inv-expirado").then().statusCode(200);
        Invitation inv = store.invitations.get("inv-expirado");
        Assertions.assertTrue(inv.expiresAt.isAfter(Instant.now()),
                "convite expirado reenviado deve voltar a ser valido");
    }

    @Test
    public void maximoDe3Reenvios() {
        seed();
        resend("u-admin", "inv-esgotado")
                .then().statusCode(422).body("code", equalTo("RESEND_LIMIT_REACHED"));
        Assertions.assertEquals(3, store.invitations.get("inv-esgotado").resendCount,
                "resendCount nao deve passar de 3");
    }

    @Test
    public void memberNaoPodeReenviar() {
        seed();
        resend("u-member", "inv-ok")
                .then().statusCode(403).body("code", equalTo("FORBIDDEN_ROLE"));
        Assertions.assertEquals(0, store.invitations.get("inv-ok").resendCount);
    }

    @Test
    public void auditoriaRegistraReenvio() {
        seed();
        resend("u-admin", "inv-ok").then().statusCode(200);
        boolean found = store.auditLog.stream().anyMatch(a ->
                "INVITATION_RESENT".equals(a.action)
                        && "u-admin".equals(a.actorId)
                        && "inv-ok".equals(a.targetId));
        Assertions.assertTrue(found, "audit log deve conter INVITATION_RESENT com target inv-ok");
    }
}
