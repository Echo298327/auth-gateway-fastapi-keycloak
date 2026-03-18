package com.authgateway.keycloak.mfa;

import org.keycloak.models.KeycloakSession;
import org.keycloak.services.resource.RealmResourceProvider;
import jakarta.ws.rs.Path;

/**
 * Main MFA Resource Provider that handles routing to TOTP and authentication endpoints.
 * Routes:
 * - /mfa/totp/* -> TotpResource (enrollment, verification, removal)
 * - /mfa/auth/* -> AuthenticationResource (password validation)
 */
public class MfaResourceProvider implements RealmResourceProvider {

    private final KeycloakSession session;

    public MfaResourceProvider(KeycloakSession session) {
        this.session = session;
    }

    @Override
    public Object getResource() {
        // Return a parent resource that routes to sub-resources
        return new MfaRootResource(session);
    }

    @Override
    public void close() {
        // Cleanup if needed
    }
    
    /**
     * Root resource that routes to sub-resources.
     */
    public static class MfaRootResource {
        private final KeycloakSession session;
        
        public MfaRootResource(KeycloakSession session) {
            this.session = session;
        }
        
        @Path("/totp")
        public TotpResource getTotpResource() {
            return new TotpResource(session);
        }
        
        @Path("/auth")
        public AuthenticationResource getAuthResource() {
            return new AuthenticationResource(session);
        }
    }
}
