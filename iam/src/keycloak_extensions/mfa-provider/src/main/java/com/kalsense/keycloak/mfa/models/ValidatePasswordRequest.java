package com.kalsense.keycloak.mfa.models;

/**
 * Request model for password validation.
 */
public class ValidatePasswordRequest {
    
    private String username;
    private String password;
    
    public ValidatePasswordRequest() {}
    
    public String getUsername() {
        return username;
    }
    
    public void setUsername(String username) {
        this.username = username;
    }
    
    public String getPassword() {
        return password;
    }
    
    public void setPassword(String password) {
        this.password = password;
    }
}
