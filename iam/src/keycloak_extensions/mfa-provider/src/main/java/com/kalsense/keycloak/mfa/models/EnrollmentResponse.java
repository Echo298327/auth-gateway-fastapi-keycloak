package com.kalsense.keycloak.mfa.models;

/**
 * Response model for TOTP enrollment.
 */
public class EnrollmentResponse {
    private String secret;
    private String otpauthUrl;
    private String qrCodeDataUrl;
    private String issuer;
    private int period;
    private int digits;
    private String algorithm;

    public EnrollmentResponse() {
    }

    public String getSecret() {
        return secret;
    }

    public void setSecret(String secret) {
        this.secret = secret;
    }

    public String getOtpauthUrl() {
        return otpauthUrl;
    }

    public void setOtpauthUrl(String otpauthUrl) {
        this.otpauthUrl = otpauthUrl;
    }

    public String getQrCodeDataUrl() {
        return qrCodeDataUrl;
    }

    public void setQrCodeDataUrl(String qrCodeDataUrl) {
        this.qrCodeDataUrl = qrCodeDataUrl;
    }

    public String getIssuer() {
        return issuer;
    }

    public void setIssuer(String issuer) {
        this.issuer = issuer;
    }

    public int getPeriod() {
        return period;
    }

    public void setPeriod(int period) {
        this.period = period;
    }

    public int getDigits() {
        return digits;
    }

    public void setDigits(int digits) {
        this.digits = digits;
    }

    public String getAlgorithm() {
        return algorithm;
    }

    public void setAlgorithm(String algorithm) {
        this.algorithm = algorithm;
    }
}
