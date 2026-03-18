package com.authgateway.keycloak.mfa.models;

/**
 * Request model for TOTP enrollment.
 */
public class EnrollmentRequest {
    private String userId;

    public EnrollmentRequest() {
    }

    public EnrollmentRequest(String userId) {
        this.userId = userId;
    }

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }
}
