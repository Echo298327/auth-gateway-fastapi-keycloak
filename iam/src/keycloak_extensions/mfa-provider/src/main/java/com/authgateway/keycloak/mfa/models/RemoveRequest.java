package com.authgateway.keycloak.mfa.models;

/**
 * Request model for TOTP removal.
 */
public class RemoveRequest {
    private String userId;

    public RemoveRequest() {
    }

    public RemoveRequest(String userId) {
        this.userId = userId;
    }

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }
}
