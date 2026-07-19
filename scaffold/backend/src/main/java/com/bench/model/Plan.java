package com.bench.model;

public enum Plan {
    FREE(5), PRO(50), ENTERPRISE(null);

    /** null = ilimitado */
    public final Integer maxUsers;

    Plan(Integer maxUsers) {
        this.maxUsers = maxUsers;
    }
}
