package com.bench;

import com.bench.model.Plan;
import com.bench.model.Tenant;
import com.bench.store.InMemoryStore;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;

@QuarkusTest
public class SmokeTest {

    @Inject
    InMemoryStore store;

    @Test
    public void storeWorks() {
        store.reset();
        Tenant t = new Tenant();
        t.id = "t1";
        t.name = "Acme";
        t.plan = Plan.FREE;
        store.tenants.put(t.id, t);
        Assertions.assertEquals(1, store.tenants.size());
        Assertions.assertEquals(Integer.valueOf(5), Plan.FREE.maxUsers);
    }

    @Test
    public void httpBoots() {
        given().when().get("/definitely-not-here").then().statusCode(404);
    }
}
