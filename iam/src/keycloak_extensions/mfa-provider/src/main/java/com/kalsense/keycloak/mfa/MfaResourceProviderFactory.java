package com.kalsense.keycloak.mfa;

import org.keycloak.Config;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.KeycloakSessionFactory;
import org.keycloak.services.resource.RealmResourceProvider;
import org.keycloak.services.resource.RealmResourceProviderFactory;

/**
 * Factory for creating MFA Resource Provider instances.
 * This is registered as a Keycloak SPI and loaded at startup.
 */
public class MfaResourceProviderFactory implements RealmResourceProviderFactory {

    public static final String ID = "mfa";

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public RealmResourceProvider create(KeycloakSession session) {
        return new MfaResourceProvider(session);
    }

    @Override
    public void init(Config.Scope config) {
        // Initialize any configuration if needed
    }

    @Override
    public void postInit(KeycloakSessionFactory factory) {
        // Post-initialization hook if needed
    }

    @Override
    public void close() {
        // Cleanup resources if needed
    }
}
