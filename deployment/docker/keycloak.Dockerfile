FROM quay.io/keycloak/keycloak:26.5.2 AS builder

# Copy the MFA provider JAR
COPY iam/src/keycloak_extensions/mfa-provider/target/mfa-provider-*.jar /opt/keycloak/providers/

# Build Keycloak with the provider
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:26.5.2

# Copy built providers from builder
COPY --from=builder /opt/keycloak/lib/quarkus/ /opt/keycloak/lib/quarkus/
COPY --from=builder /opt/keycloak/providers/ /opt/keycloak/providers/

# Copy the custom configuration file
COPY deployment/docker/keycloak.conf /opt/keycloak/conf
