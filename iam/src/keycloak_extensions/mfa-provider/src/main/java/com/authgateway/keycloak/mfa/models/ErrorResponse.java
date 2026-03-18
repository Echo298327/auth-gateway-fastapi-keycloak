package com.authgateway.keycloak.mfa.models;

/**
 * Generic error response model.
 */
public class ErrorResponse {
    
    private String error;
    
    public ErrorResponse() {}
    
    public ErrorResponse(String error) {
        this.error = error;
    }
    
    public String getError() {
        return error;
    }
    
    public void setError(String error) {
        this.error = error;
    }
}
