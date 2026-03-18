# Build & Deployment Guide

## 🚀 Quick Start

### 1. Build the MFA Provider

```bash
cd keycloak_extensions/mfa-provider
mvn clean package
```

This will create: `target/mfa-provider-1.0.0.jar`

### 2. Build Custom Keycloak Image

```bash
cd keycloak_extensions
docker build -f Dockerfile.keycloak -t keycloak-custom:latest .
```

### 3. Run Locally

```bash
docker run -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  keycloak-custom:latest start-dev
```

### 4. Test the API

```bash
# Get admin token
TOKEN=$(curl -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" | jq -r '.access_token')

# Create a test user first (if needed)
curl -X POST http://localhost:8080/admin/realms/master/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "enabled": true,
    "credentials": [{
      "type": "password",
      "value": "testpass",
      "temporary": false
    }]
  }'

# Enroll user in MFA
curl -X POST http://localhost:8080/realms/master/mfa/totp/enroll \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"userId": "testuser"}' | jq
```

---

## 📦 Production Deployment

### Option 1: Docker Compose

Create/update `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: keycloak_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  keycloak:
    build:
      context: ./keycloak_extensions
      dockerfile: Dockerfile.keycloak
    ports:
      - "8080:8080"
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD:-admin}
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: keycloak_password
      KC_HOSTNAME: ${KEYCLOAK_HOSTNAME:-localhost}
      KC_HTTP_ENABLED: "true"
      KC_HOSTNAME_STRICT: "false"
      KC_HOSTNAME_STRICT_HTTPS: "false"
      KC_PROXY: edge
    command: start
    depends_on:
      - postgres

volumes:
  postgres_data:
```

Deploy:

```bash
docker-compose up -d
```

### Option 2: Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: keycloak
  namespace: auth
spec:
  replicas: 2
  selector:
    matchLabels:
      app: keycloak
  template:
    metadata:
      labels:
        app: keycloak
    spec:
      containers:
      - name: keycloak
        image: your-registry.com/keycloak-custom:1.0.0
        ports:
        - name: http
          containerPort: 8080
        env:
        - name: KEYCLOAK_ADMIN
          valueFrom:
            secretKeyRef:
              name: keycloak-admin
              key: username
        - name: KEYCLOAK_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: keycloak-admin
              key: password
        - name: KC_DB
          value: "postgres"
        - name: KC_DB_URL
          value: "jdbc:postgresql://postgres-service:5432/keycloak"
        - name: KC_HOSTNAME
          value: "auth.yourdomain.com"
        - name: KC_PROXY
          value: "edge"
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 90
          periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: keycloak
  namespace: auth
spec:
  selector:
    app: keycloak
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: keycloak
  namespace: auth
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - auth.yourdomain.com
    secretName: keycloak-tls
  rules:
  - host: auth.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: keycloak
            port:
              number: 8080
```

---

## 🔄 CI/CD Integration

### GitHub Actions Example

`.github/workflows/build-keycloak.yml`:

```yaml
name: Build Keycloak Extensions

on:
  push:
    branches: [main, develop]
    paths:
      - 'keycloak_extensions/**'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up JDK 17
        uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: maven
      
      - name: Build MFA Provider
        run: |
          cd keycloak_extensions/mfa-provider
          mvn clean package
      
      - name: Build Docker Image
        run: |
          cd keycloak_extensions
          docker build -f Dockerfile.keycloak \
            -t ${{ secrets.DOCKER_REGISTRY }}/keycloak-custom:${{ github.sha }} \
            -t ${{ secrets.DOCKER_REGISTRY }}/keycloak-custom:latest .
      
      - name: Push to Registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login ${{ secrets.DOCKER_REGISTRY }} -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push ${{ secrets.DOCKER_REGISTRY }}/keycloak-custom:${{ github.sha }}
          docker push ${{ secrets.DOCKER_REGISTRY }}/keycloak-custom:latest
```

### Jenkins Pipeline

`Jenkinsfile`:

```groovy
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'your-registry.com'
        IMAGE_NAME = 'keycloak-custom'
    }
    
    stages {
        stage('Build Maven') {
            steps {
                dir('keycloak_extensions/mfa-provider') {
                    sh 'mvn clean package'
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                dir('keycloak_extensions') {
                    script {
                        def image = docker.build("${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}", "-f Dockerfile.keycloak .")
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                sh '''
                    kubectl set image deployment/keycloak \
                      keycloak=${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER} \
                      -n staging
                '''
            }
        }
    }
}
```

---

## 🔧 Development Workflow

### Local Development Setup

```bash
# 1. Clone and navigate
cd keycloak_extensions/mfa-provider

# 2. Build in watch mode (optional, requires maven plugin)
mvn compile quarkus:dev

# 3. Or build manually after changes
mvn clean package

# 4. Restart Keycloak with new JAR
docker restart keycloak
# or
docker-compose restart keycloak
```

### Testing Changes

```bash
# Build
mvn clean package

# Copy to running Keycloak
docker cp target/mfa-provider-1.0.0.jar keycloak:/opt/keycloak/providers/

# Rebuild and restart
docker exec keycloak /opt/keycloak/bin/kc.sh build
docker restart keycloak

# Check logs
docker logs -f keycloak
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KEYCLOAK_ADMIN` | Admin username | `admin` |
| `KEYCLOAK_ADMIN_PASSWORD` | Admin password | - |
| `KC_DB` | Database type | `postgres` |
| `KC_DB_URL` | Database JDBC URL | - |
| `KC_HOSTNAME` | Public hostname | `localhost` |
| `KC_PROXY` | Proxy mode (edge/passthrough) | - |
| `KC_HTTP_ENABLED` | Enable HTTP | `false` |

### Maven Properties

In `pom.xml`:

```xml
<properties>
    <keycloak.version>24.0.2</keycloak.version>
</properties>
```

Update this when upgrading Keycloak.

---

## 🐛 Troubleshooting

### Provider not loading

```bash
# Check if JAR exists
docker exec keycloak ls -la /opt/keycloak/providers/

# Check Keycloak logs
docker logs keycloak 2>&1 | grep -i "mfa"

# Verify provider is registered
# Admin Console → Server Info → Providers → Look for "mfa"
```

### Build fails

```bash
# Clean Maven cache
mvn clean
rm -rf ~/.m2/repository/org/keycloak

# Force update dependencies
mvn clean install -U
```

### Docker build fails

```bash
# Ensure JAR is built first
cd mfa-provider
mvn clean package
cd ..

# Build with no cache
docker build --no-cache -f Dockerfile.keycloak -t keycloak-custom .
```

---

## 📊 Monitoring

### Health Checks

```bash
# Readiness
curl http://localhost:8080/health/ready

# Liveness
curl http://localhost:8080/health/live

# Metrics (if enabled)
curl http://localhost:8080/metrics
```

### Logs

```bash
# All logs
docker logs -f keycloak

# Only MFA provider logs
docker logs keycloak 2>&1 | grep "com.kalsense.keycloak.mfa"

# Kubernetes
kubectl logs -f deployment/keycloak -n auth
```

---

## 🔐 Security Checklist

- [ ] Change default admin password
- [ ] Use HTTPS in production (set `KC_HTTPS_ENABLED=true`)
- [ ] Set `KC_HOSTNAME_STRICT=true` in production
- [ ] Configure proper database credentials
- [ ] Enable brute force detection
- [ ] Set up rate limiting
- [ ] Review OTP policy settings
- [ ] Enable audit logging
- [ ] Regularly update Keycloak version

---

For more details, see [README.md](README.md) and [mfa-provider/README.md](mfa-provider/README.md).
