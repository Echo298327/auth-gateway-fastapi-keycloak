package com.authgateway.keycloak.mfa.models;

/**
 * Response model for TOTP removal.
 */
public class RemoveResponse {
    private boolean success;
    private String message;

    public RemoveResponse() {
    }

    public RemoveResponse(boolean success, String message) {
        this.success = success;
        this.message = message;
    }

    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
