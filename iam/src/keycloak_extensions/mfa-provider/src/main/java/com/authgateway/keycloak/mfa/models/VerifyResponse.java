package com.authgateway.keycloak.mfa.models;

/**
 * Response model for OTP verification.
 */
public class VerifyResponse {
    private boolean verified;
    private String message;

    public VerifyResponse() {
    }

    public VerifyResponse(boolean verified, String message) {
        this.verified = verified;
        this.message = message;
    }

    public boolean isVerified() {
        return verified;
    }

    public void setVerified(boolean verified) {
        this.verified = verified;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
