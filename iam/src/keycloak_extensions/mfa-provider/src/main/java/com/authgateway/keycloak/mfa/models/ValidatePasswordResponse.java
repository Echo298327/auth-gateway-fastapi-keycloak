package com.authgateway.keycloak.mfa.models;

/**
 * Response model for password validation.
 * 
 * SECURITY: Only returns valid/invalid, no specific reason to prevent account enumeration.
 * 
 * Possible values:
 * - valid: true - Username and password are correct
 * - valid: false - Either username or password is incorrect (doesn't specify which)
 */
public class ValidatePasswordResponse {
    
    private boolean valid;
    
    public ValidatePasswordResponse() {}
    
    public ValidatePasswordResponse(boolean valid) {
        this.valid = valid;
    }
    
    public boolean isValid() {
        return valid;
    }
    
    public void setValid(boolean valid) {
        this.valid = valid;
    }
}
