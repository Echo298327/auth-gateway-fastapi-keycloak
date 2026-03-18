package com.authgateway.keycloak.mfa.models;

/**
 * Request model for OTP verification.
 */
public class VerifyRequest {
    private String userId;
    private String otp;

    public VerifyRequest() {
    }

    public VerifyRequest(String userId, String otp) {
        this.userId = userId;
        this.otp = otp;
    }

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getOtp() {
        return otp;
    }

    public void setOtp(String otp) {
        this.otp = otp;
    }
}
