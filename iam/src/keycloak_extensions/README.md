# Keycloak Extensions - Kal-Sense

This directory contains custom Keycloak extensions (SPIs/Providers) for Kal-Sense that extend Keycloak functionality beyond what's available out-of-the-box.

**Note:** Kal-Sense is a multi-tenant application. Each tenant uses a separate Keycloak realm, and these extensions work seamlessly across all realms.

## 📁 Structure

```
keycloak_extensions/
├── mfa-provider/           # TOTP/2FA enrollment API
├── Dockerfile.keycloak     # Custom Keycloak image with extensions
└── README.md               # This file
```

## 🔌 Available Extensions

### 1. MFA Provider (`mfa-provider/`)

**Purpose:** Provides REST API endpoints for headless TOTP/2FA enrollment and verification without using Keycloak UI.

**Endpoints:**
- `POST /realms/{realm}/mfa/totp/enroll` - Generate and register TOTP secret for a user
- `POST /realms/{realm}/mfa/totp/verify` - Verify OTP code during enrollment
- `DELETE /realms/{realm}/mfa/totp/remove` - Remove TOTP credential from user

**Use Case:** React/SPA applications that want to display QR codes and manage 2FA without redirecting to Keycloak login pages.

See [mfa-provider/README.md](./mfa-provider/README.md) for detailed documentation.

---

## 🚀 Quick Start

### Prerequisites

- Java 17+
- Maven 3.8+
- Docker (for deployment)

### Build All Extensions

```bash
cd keycloak_extensions
mvn clean package
```

This will build all extensions and create JAR files in `*/target/` directories.

### Local Development with Docker

Build custom Keycloak image with extensions:

```bash
docker build -f Dockerfile.keycloak -t keycloak-custom:latest .
```

Run locally:

```bash
docker run -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  keycloak-custom:latest start-dev
```

Access Keycloak: http://localhost:8080

---

## 📦 Deployment

### Option 1: Docker Compose (Recommended)

Update your `docker-compose.yml`:

```yaml
services:
  keycloak:
    build:
      context: ./keycloak_extensions
      dockerfile: Dockerfile.keycloak
    ports:
      - "8080:8080"
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: ${DB_USER}
      KC_DB_PASSWORD: ${DB_PASSWORD}
      KC_HOSTNAME: ${KEYCLOAK_HOSTNAME}
    command: start --optimized
```

### Option 2: Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: keycloak
spec:
  template:
    spec:
      containers:
      - name: keycloak
        image: your-registry/keycloak-custom:latest
        volumeMounts:
        - name: providers
          mountPath: /opt/keycloak/providers
      volumes:
      - name: providers
        configMap:
          name: keycloak-providers
```

### Option 3: Manual Installation

Copy JAR files to Keycloak:

```bash
cp mfa-provider/target/mfa-provider-*.jar /opt/keycloak/providers/
/opt/keycloak/bin/kc.sh build
/opt/keycloak/bin/kc.sh start
```

---

## 🔧 Development

### Adding a New Extension

1. Create new Maven module:

```bash
cd keycloak_extensions
mkdir my-new-provider
cd my-new-provider
```

2. Create `pom.xml` with Keycloak dependencies

3. Implement your SPI:
   - `*Provider.java` - Main logic
   - `*ProviderFactory.java` - Factory for creating provider instances

4. Add to parent POM (if using multi-module)

5. Build and test:

```bash
mvn clean package
docker build -f ../Dockerfile.keycloak -t keycloak-test .
docker run -p 8080:8080 keycloak-test start-dev
```

### Testing Extensions

Each extension should have unit tests:

```bash
cd mfa-provider
mvn test
```

For integration tests, see `mfa-provider/tests/` directory.

---

## 📚 Resources

- [Keycloak SPI Documentation](https://www.keycloak.org/docs/latest/server_development/)
- [Keycloak Provider Interfaces](https://github.com/keycloak/keycloak/tree/main/server-spi)
- [Building Custom Providers](https://www.keycloak.org/docs/latest/server_development/#implementing-an-spi)

---

## 🔄 Version Compatibility

| Extension Version | Keycloak Version | Status |
|------------------|------------------|---------|
| 1.0.0            | 24.0.x          | ✅ Active |
| 1.0.0            | 23.0.x          | ✅ Compatible |
| 1.0.0            | 22.0.x          | ⚠️ Not tested |

---

## ⚠️ Important Notes

### Upgrade Strategy

When upgrading Keycloak major versions:

1. Check [Keycloak Migration Guide](https://www.keycloak.org/docs/latest/upgrading/)
2. Update `keycloak.version` in `pom.xml`
3. Rebuild all extensions: `mvn clean package`
4. Run tests
5. Test in staging environment before production

### Security Considerations

- Extensions run **inside** Keycloak with full access to user data
- Always validate input parameters
- Use Keycloak's built-in authorization checks
- Follow principle of least privilege
- Audit log all sensitive operations

### Performance

- Extensions are loaded at Keycloak startup
- Code is executed synchronously in request handling
- Avoid blocking operations (use async where possible)
- Consider caching for frequently accessed data

---

## 🤝 Contributing

When adding new extensions:

1. Follow existing code structure
2. Include comprehensive README in extension directory
3. Add unit tests (minimum 80% coverage)
4. Document all API endpoints
5. Update this README with new extension info

---

## 📄 License

Same as parent project.

---

## 🆘 Troubleshooting

### Extension not loading

Check logs:
```bash
docker logs keycloak 2>&1 | grep -i "provider"
```

Verify JAR is in providers directory:
```bash
docker exec keycloak ls -la /opt/keycloak/providers/
```

### Build failed after Keycloak upgrade

1. Update Keycloak version in POM
2. Check for API changes in [Keycloak GitHub](https://github.com/keycloak/keycloak/releases)
3. Rebuild: `mvn clean package -U`

### API returns 404

Ensure:
- Extension is loaded (check Admin Console → Server Info → Providers)
- Realm name in URL is correct
- Endpoint path matches the @Path annotation

---

For extension-specific issues, see individual README files in each provider directory.
