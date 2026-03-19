FROM quay.io/keycloak/keycloak:26.5.2 AS builder

COPY deployment/docker/keycloak.conf /opt/keycloak/conf/keycloak.conf
COPY iam/src/keycloak_extensions/mfa-provider/target/mfa-provider-*.jar /opt/keycloak/providers/

RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:26.5.2

COPY --from=builder /opt/keycloak/lib/quarkus/ /opt/keycloak/lib/quarkus/
COPY --from=builder /opt/keycloak/providers/ /opt/keycloak/providers/
COPY deployment/docker/keycloak.conf /opt/keycloak/conf/keycloak.conf
