# MFA Provider Architecture

## Overview

This is a Keycloak Service Provider Interface (SPI) extension that adds headless TOTP/2FA management capabilities via REST endpoints.

**Technology Stack:**
- Java 17
- Keycloak 26.3.3 APIs
- ZXing (QR code generation)
- JAX-RS (REST endpoints)
- Maven (build tool)

---

## Project Structure

```
mfa-provider/
├── pom.xml                                    # Maven configuration
├── README.md                                  # API documentation
├── ARCHITECTURE.md                            # This file
│
├── src/main/java/com/kalsense/keycloak/mfa/
│   │
│   ├── MfaResourceProviderFactory.java       # SPI Factory - Creates provider instances
│   ├── MfaResourceProvider.java              # SPI Provider - Registers REST resource
│   ├── TotpResource.java                     # REST Endpoints - Handles HTTP requests
│   │
│   ├── utils/
│   │   └── TotpManager.java                  # Core Logic - Secret generation, QR codes, verification
│   │
│   └── models/                                # DTOs (Data Transfer Objects)
│       ├── EnrollmentRequest.java            # POST /enroll request body
│       ├── EnrollmentResponse.java           # POST /enroll response body
│       ├── VerifyRequest.java                # POST /verify request body
│       ├── VerifyResponse.java               # POST /verify response body
│       ├── RemoveRequest.java                # DELETE /remove request body
│       ├── RemoveResponse.java               # DELETE /remove response body
│       └── ErrorResponse.java                # Error response body
│
└── src/main/resources/
    └── META-INF/services/
        └── org.keycloak.services.resource.RealmResourceProviderFactory
                                               # SPI registration file
```

---

## Key Components

### 1. MfaResourceProviderFactory

**Purpose:** Keycloak SPI factory that creates provider instances.

**Responsibilities:**
- Implements `RealmResourceProviderFactory`
- Provides provider ID: `"mfa"`
- Creates `MfaResourceProvider` instances for each realm

**Keycloak Integration:**
- Registered via `META-INF/services/org.keycloak.services.resource.RealmResourceProviderFactory`
- Loaded automatically when Keycloak starts
- One instance per Keycloak deployment

**Code Flow:**
```
Keycloak Startup
  → Reads META-INF/services file
  → Finds MfaResourceProviderFactory class
  → Calls create() for each realm
  → Returns MfaResourceProvider instance
```

---

### 2. MfaResourceProvider

**Purpose:** Registers the REST resource with Keycloak's JAX-RS runtime.

**Responsibilities:**
- Implements `RealmResourceProvider`
- Returns `TotpResource` instance when endpoint is accessed
- Provides provider metadata

**URL Mapping:**
```
/realms/{realm}/mfa → MfaResourceProvider.getResource()
                   → Returns TotpResource instance
                   → TotpResource handles /enroll, /verify, /remove
```

**Lifecycle:**
- Created once per realm per request
- Short-lived (request-scoped)
- Closed after request completes

---

### 3. TotpResource

**Purpose:** Defines the REST API endpoints for MFA operations.

**Endpoints:**

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| POST | `/mfa/enroll` | `enroll()` | Generate secret + QR code |
| POST | `/mfa/verify` | `verify()` | Verify OTP code |
| DELETE | `/mfa/remove` | `remove()` | Remove TOTP credential |

**Responsibilities:**
- Request validation (check required fields)
- User lookup (by Keycloak UUID)
- Delegate to `TotpManager` for business logic
- Build JSON responses
- Error handling and logging

**Dependencies:**
- `KeycloakSession` - Access to Keycloak APIs
- `TotpManager` - Core TOTP logic
- Request/Response DTOs

**Example Flow (Enrollment):**
```
POST /realms/kal-sense/mfa/enroll
  → TotpResource.enroll()
  → Validate request (userId present?)
  → Get realm and user from session
  → Create TotpManager
  → Call totpManager.generateTotpSecret(user)
  → Return EnrollmentResponse with QR code
```

---

### 4. TotpManager

**Purpose:** Core business logic for TOTP operations.

**Key Responsibilities:**

#### Secret Generation
- Creates cryptographically secure random secrets (20 bytes)
- Encodes as Base32 (RFC 4648)
- Stores in-memory for pending enrollments
- **Reuses existing pending secret** if enrollment called multiple times

#### QR Code Generation
- Builds `otpauth://` URI (Google Authenticator format)
- Generates QR code using ZXing library
- Converts to Base64-encoded PNG data URL
- Returns `data:image/png;base64,...` format

#### OTP Verification
- **Two modes:**
  - **Initial Setup:** Verifies against pending secret, then saves to Keycloak
  - **Login:** Verifies against stored credential in Keycloak
- Uses `TimeBasedOTP` from Keycloak API
- Time window: **3 periods** (~90 seconds validity)
- Base32 decodes secret before verification

#### Credential Management
- Creates `OTPCredentialModel` with secret + settings
- Stores via Keycloak's `CredentialManager` API
- Retrieves existing credentials for verification
- Removes credentials when requested

**Key Methods:**

```java
// Generate secret and QR code
public EnrollmentResponse generateTotpSecret(UserModel user)

// Verify OTP (handles both setup and login)
public boolean verifyAndSaveOtp(UserModel user, String otpCode)

// Remove TOTP credential
public boolean removeTotpCredential(UserModel user)

// Internal utilities
private String generateSecret()
private String base32Encode(byte[] data)
private byte[] base32Decode(String encoded)
private String buildOtpauthUrl(...)
private String generateQrCodeDataUrl(...)
private void saveOtpCredential(UserModel user, String secret)
```

**In-Memory State:**
```java
private static final Map<String, String> pendingSecrets = new HashMap<>();
// Key: userId (Keycloak UUID)
// Value: Base32 secret
// Purpose: Store secrets during enrollment until verified
// Lifecycle: Cleared after successful verification
```

---

### 5. Model Classes (DTOs)

Simple POJOs for request/response serialization.

**EnrollmentRequest:**
```json
{ "userId": "keycloak-uuid" }
```

**EnrollmentResponse:**
```json
{
  "secret": "BASE32SECRET",
  "otpauthUrl": "otpauth://...",
  "qrCodeDataUrl": "data:image/png;base64,...",
  "issuer": "Kal-Sense",
  "period": 30,
  "digits": 6,
  "algorithm": "SHA1"
}
```

**VerifyRequest:**
```json
{ "userId": "keycloak-uuid", "otp": "123456" }
```

**VerifyResponse:**
```json
{ "verified": true/false, "message": "..." }
```

**RemoveRequest:**
```json
{ "userId": "keycloak-uuid" }
```

**RemoveResponse:**
```json
{ "success": true, "message": "TOTP credential removed successfully" }
```

---

## Data Flow

### Enrollment Flow

```
Frontend (React)
  │
  │ POST /realms/kal-sense/mfa/enroll
  │ { "userId": "abc-123" }
  ↓
API Gateway (Python)
  │
  │ Forwards request with admin token
  ↓
Keycloak
  │
  │ Routes to /mfa → MfaResourceProvider
  ↓
TotpResource.enroll()
  │
  │ 1. Validate request
  │ 2. Find user by UUID
  │ 3. Create TotpManager
  ↓
TotpManager.generateTotpSecret()
  │
  │ 1. Check pendingSecrets map
  │ 2. If exists → reuse, else → generate new
  │ 3. Build otpauth:// URL
  │ 4. Generate QR code (ZXing)
  │ 5. Convert to Base64 PNG
  │ 6. Store in pendingSecrets
  ↓
Return EnrollmentResponse
  │
  │ { "secret": "...", "qrCodeDataUrl": "...", ... }
  ↓
API Gateway
  │
  │ Returns to frontend
  ↓
Frontend
  │
  │ Displays QR code
  │ User scans with Google Authenticator
```

### Verification Flow (Initial Setup)

```
User scans QR code with authenticator app
  ↓
App generates 6-digit OTP code
  ↓
User enters code in frontend
  │
  │ POST /realms/kal-sense/mfa/verify
  │ { "userId": "abc-123", "otp": "123456" }
  ↓
TotpResource.verify()
  │
  │ 1. Validate request
  │ 2. Find user by UUID
  │ 3. Create TotpManager
  ↓
TotpManager.verifyAndSaveOtp()
  │
  │ 1. Check if user has existing credential
  │    → No? Check pendingSecrets (initial setup)
  │ 2. Decode Base32 secret
  │ 3. Create TimeBasedOTP (window=3)
  │ 4. Validate OTP code
  │ 5. If valid → save credential to Keycloak
  │ 6. Remove from pendingSecrets
  ↓
Return VerifyResponse
  │
  │ { "verified": true, "message": "..." }
  ↓
API Gateway
  │
  │ Removes "CONFIGURE_TOTP" required action
  │ Returns "setup_complete" to frontend
```

### Verification Flow (Login)

```
User logs in with username + password + OTP
  │
  │ POST /realms/kal-sense/mfa/verify
  │ { "userId": "abc-123", "otp": "789012" }
  ↓
TotpResource.verify()
  ↓
TotpManager.verifyAndSaveOtp()
  │
  │ 1. Check if user has existing credential
  │    → Yes? Retrieve from Keycloak
  │ 2. Get stored secret from OTPCredentialModel
  │ 3. Decode Base32 secret
  │ 4. Create TimeBasedOTP (window=3)
  │ 5. Validate OTP code
  │    (No saving - credential already exists)
  ↓
Return VerifyResponse
  │
  │ { "verified": true, "message": "..." }
  ↓
API Gateway
  │
  │ Uses admin impersonation to get token
  │ Returns token to user
```

---

## Keycloak Integration Points

### 1. Credential Manager API

```java
// Get user's credential manager
user.credentialManager()

// Create and store OTP credential
OTPCredentialModel credential = OTPCredentialModel.createTOTP(
    secret, digits, period, algorithm
);
user.credentialManager().createStoredCredential(credential);

// Get existing credentials
List<CredentialModel> credentials = user.credentialManager()
    .getStoredCredentialsByTypeStream(OTPCredentialModel.TYPE)
    .toList();

// Remove credential
user.credentialManager().removeStoredCredentialById(credentialId);
```

### 2. TimeBasedOTP API

```java
import org.keycloak.models.utils.TimeBasedOTP;

// Create TOTP validator with time window
TimeBasedOTP totp = new TimeBasedOTP(
    algorithm,  // "SHA1"
    digits,     // 6
    period,     // 30 seconds
    window      // 3 (accept previous/current/next period)
);

// Validate OTP code
boolean valid = totp.validateTOTP(otpCode, secretBytes);
```

### 3. User and Session APIs

```java
// Get realm and session
KeycloakSession session = // injected by Keycloak
RealmModel realm = session.getContext().getRealm();

// Find user
UserModel user = session.users().getUserById(realm, userId);
UserModel user = session.users().getUserByUsername(realm, username);
```

---

## Security Considerations

### Cryptographic Security

- **Secret Generation:** Uses `SecureRandom` for cryptographically secure randomness
- **Secret Length:** 20 bytes (160 bits) as recommended by RFC 6238
- **Algorithm:** SHA-1 HMAC (TOTP standard, despite SHA-1 deprecation for other uses)
- **Time Window:** 3 periods prevents clock skew issues while maintaining security

### Secret Storage

- **Pending Secrets:** Stored in-memory (cleared after verification or server restart)
- **Permanent Secrets:** Stored in Keycloak database (encrypted by Keycloak)
- **No plaintext secrets in logs:** Only logged at debug level

### Replay Attack Prevention

- Keycloak tracks used OTP codes internally
- Same code cannot be used twice within the time window

### Input Validation

- User ID required and validated
- OTP code validated (must be 6 digits)
- User existence checked before operations

---

## Error Handling

### HTTP Status Codes

| Code | Scenario | Example |
|------|----------|---------|
| 200 | Success | OTP verified, credential saved |
| 400 | Invalid request | Missing userId, invalid OTP |
| 404 | Not found | User doesn't exist |
| 500 | Server error | Failed to generate QR code |

### Logging Levels

- **INFO:** Successful operations (enrolled, verified, removed)
- **WARN:** Invalid OTP, missing credentials
- **ERROR:** Unexpected exceptions, QR generation failures
- **DEBUG:** Detailed OTP validation (secret, code, result)

### Exception Handling

All endpoints wrapped in try-catch:
```java
try {
    // Business logic
    return Response.ok(successResponse).build();
} catch (Exception e) {
    logger.error("Operation failed", e);
    return Response.serverError()
        .entity(new ErrorResponse(e.getMessage()))
        .build();
}
```

---

## Performance Considerations

### QR Code Generation

- ZXing library is fast (~10ms per QR code)
- Images cached as Base64 strings (no file I/O)
- QR codes generated on-demand (not pre-computed)

### Secret Storage

- In-memory map for pending secrets (fast O(1) lookup)
- Database persistence for permanent credentials
- No caching layer needed (Keycloak handles it)

### Concurrency

- Stateless design (except pendingSecrets map)
- Thread-safe operations via Keycloak APIs
- No custom locking required

---

## Testing

### Manual Testing

See `README.md` for cURL examples.

### Unit Testing

```bash
mvn test
```

**Coverage:**
- Secret generation and encoding
- QR code generation
- OTP verification logic
- Base32 encode/decode

### Integration Testing

1. Deploy to local Keycloak
2. Use Postman/cURL to test endpoints
3. Test with real authenticator app (Google Authenticator, Authy)

---

## Build Process

### Maven Lifecycle

```
mvn clean          → Deletes target/ directory
mvn compile        → Compiles Java sources
mvn package        → Creates JAR with dependencies (fat JAR)
mvn install        → Installs to local Maven repo
```

### Maven Shade Plugin

- Bundles all dependencies into one JAR
- Handles conflicting classes
- Output: `target/mfa-provider-1.0.0.jar` (~1MB)

### Docker Build Integration

```dockerfile
# In Dockerfile.keycloak
COPY mfa-provider/target/mfa-provider-*.jar /opt/keycloak/providers/
RUN /opt/keycloak/bin/kc.sh build
```

Keycloak's `kc.sh build` command:
- Scans `/opt/keycloak/providers/` for JARs
- Loads SPI providers
- Optimizes Quarkus application
- Registers REST endpoints

---

## Troubleshooting

### Common Issues

**1. Provider not loaded**
- Check JAR is in `/opt/keycloak/providers/`
- Verify `kc.sh build` was executed
- Check logs for SPI registration message

**2. 404 on endpoints**
- Verify realm name in URL
- Check provider ID is "mfa"
- Ensure Keycloak restarted after JAR deployment

**3. QR code generation fails**
- Verify ZXing dependency in JAR
- Check logs for stack traces
- Test secret generation separately

**4. OTP always invalid**
- Check time synchronization
- Verify secret matches between QR and verification
- Increase time window if needed

### Debugging

Enable debug logging in Keycloak:
```bash
# In Keycloak config
log-level=DEBUG:com.kalsense.keycloak.mfa
```

Check logs:
```bash
docker logs backend_keycloak | grep "com.kalsense"
```

---

## Future Enhancements

- [ ] Support for backup codes
- [ ] SMS OTP as alternative
- [ ] WebAuthn/FIDO2 integration
- [ ] Multiple TOTP devices per user
- [ ] Admin bulk operations API
- [ ] Recovery flow for lost devices
- [ ] Prometheus metrics
- [ ] Unit test coverage >80%

---

## References

### Internal Documentation
- `README.md` - API documentation and usage
- `BUILD.md` - Build and deployment instructions

### External Resources
- [Keycloak SPI Development Guide](https://www.keycloak.org/docs/latest/server_development/)
- [RFC 6238 - TOTP Specification](https://tools.ietf.org/html/rfc6238)
- [ZXing Documentation](https://github.com/zxing/zxing)
- [Google Authenticator Key Format](https://github.com/google/google-authenticator/wiki/Key-Uri-Format)

---

**Last Updated:** January 2026  
**Keycloak Version:** 26.3.3  
**Java Version:** 17
