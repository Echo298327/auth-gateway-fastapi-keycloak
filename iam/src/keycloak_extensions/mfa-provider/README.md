# MFA Provider - Kal-Sense

REST API extension for headless TOTP/2FA enrollment and management in Keycloak for Kal-Sense.

**Multi-Tenant Support:** This extension works with Kal-Sense's multi-tenant architecture. Each tenant (realm) has independent 2FA settings and user credentials.

## 📋 Overview

This extension adds REST endpoints to Keycloak that allow applications to:
- Generate TOTP secrets for users
- Return QR codes for authenticator apps (Google Authenticator, Authy, etc.)
- Verify OTP codes during enrollment and login
- Remove TOTP credentials

**Use Case:** Kal-Sense manages 2FA enrollment within its own UI without exposing Keycloak's architecture to end-users, maintaining a seamless user experience across all tenants.

---

## 🔌 API Endpoints

All endpoints are under: `/realms/{realm}/mfa/`

### 1. Enroll User in TOTP

**POST** `/realms/{realm}/mfa/enroll`

Generates a new TOTP secret for a user and returns QR code data.

**Request:**
```json
{
  "userId": "user-keycloak-uuid"
}
```

**Response (200 OK):**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "otpauthUrl": "otpauth://totp/Kal-Sense:username?secret=JBSWY3DPEHPK3PXP&issuer=Kal-Sense&digits=6&period=30&algorithm=SHA1",
  "qrCodeDataUrl": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "issuer": "Kal-Sense",
  "period": 30,
  "digits": 6,
  "algorithm": "SHA1"
}
```

**Errors:**
- `400` - Invalid request (missing userId)
- `404` - User not found
- `500` - Failed to generate secret

**Notes:**
- If called multiple times for the same user during enrollment, it returns the **same secret** (not a new one)
- This prevents invalidating the QR code if the user refreshes the page

---

### 2. Verify OTP Code

**POST** `/realms/{realm}/mfa/verify`

Verifies an OTP code against the user's credential.

**During Initial Setup:** Verifies the code and saves the credential to Keycloak.

**During Login:** Verifies the code against the stored credential.

**Request:**
```json
{
  "userId": "user-keycloak-uuid",
  "otp": "123456"
}
```

**Response (200 OK):**
```json
{
  "verified": true,
  "message": "OTP verified successfully"
}
```

**Response (400 Bad Request):**
```json
{
  "verified": false,
  "message": "Invalid OTP code"
}
```

**Errors:**
- `400` - Invalid OTP code
- `404` - User not found

**Notes:**
- Uses a **time window of 3** (accepts codes from previous/current/next 30-second period = ~90 seconds validity)
- Automatically handles both enrollment and login scenarios

---

### 3. Remove TOTP Credential

**DELETE** `/realms/{realm}/mfa/remove`

Removes TOTP credential from user (disables 2FA).

**Request:**
```json
{
  "userId": "user-keycloak-uuid"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "TOTP credential removed successfully"
}
```

**Errors:**
- `404` - User not found or no TOTP credential exists

---

## 🔄 Integration with Kal-Sense Login Flow

The MFA system integrates with Keycloak's **Required Actions** mechanism. When an admin sets "Configure OTP" as a required action for a user, the login flow automatically handles it:

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  User Login (username + password)                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │ Has OTP Configured?│
         └────────┬───────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
       YES                  NO
        │                    │
        ▼                    ▼
┌───────────────┐    ┌──────────────────────┐
│ OTP Provided? │    │ CONFIGURE_TOTP       │
└───────┬───────┘    │ Required Action?     │
        │            └──────────┬───────────┘
   ┌────┴────┐                 │
  YES       NO          ┌───────┴────────┐
   │         │         YES              NO
   ▼         ▼          │                │
┌──────┐  ┌─────┐      ▼                ▼
│Verify│  │Ask  │  ┌────────────┐  ┌────────┐
│ OTP  │  │for  │  │Return      │  │Return  │
│      │  │OTP  │  │QR Code     │  │Token   │
└──┬───┘  └─────┘  └─────┬──────┘  └────────┘
   │                     │
   ▼                     ▼
┌──────────┐      ┌──────────────┐
│Get Token │      │Scan QR, then │
│via       │      │Login with OTP│
│Imperson  │      └──────────────┘
└──────────┘
```

### Initial Setup Flow

1. Admin sets "Configure OTP" required action for user in Keycloak
2. User logs in with username + password
3. API Gateway detects `CONFIGURE_TOTP` required action
4. Returns QR code via `/mfa/enroll`
5. User scans QR code with authenticator app
6. User logs in again with username + password + OTP code
7. API Gateway verifies OTP via `/mfa/verify`
8. If valid, removes `CONFIGURE_TOTP` required action
9. Returns "setup_complete" message
10. User can now login normally with OTP

### Regular Login Flow (After Setup)

1. User logs in with username + password + OTP code
2. API Gateway checks if user has OTP configured (before attempting Keycloak login)
3. Verifies OTP via `/mfa/verify`
4. If valid, uses Keycloak Admin API impersonation to get token
5. Returns token to user

**Why Impersonation?** Keycloak's Direct Grant (ROPC) flow with OTP has limitations. We use our custom verification endpoint + admin impersonation for a more reliable flow.

---

## 🏗️ Build & Deploy

### Prerequisites

- Maven 3.6+
- Java 17+
- Docker (for containerized deployment)

### Build

```bash
cd keycloak_extensions/mfa-provider
mvn clean package
```

Output: `target/mfa-provider-1.0.0.jar` (~1MB)

### Deploy with Docker

The project uses a custom Dockerfile that builds Keycloak with the MFA extension:

```bash
# Build the extension JAR first
cd keycloak_extensions/mfa-provider
mvn clean package

# Build Keycloak Docker image with extension
cd ../..
docker-compose -f docker-compose.minimal.yml build keycloak

# Start services
docker-compose -f docker-compose.minimal.yml up -d
```

### Verify Deployment

Check if provider is loaded:

```bash
docker logs backend_keycloak | grep -i "mfa"
```

Expected output:
```
KC-SERVICES0047: mfa (com.kalsense.keycloak.mfa.MfaResourceProviderFactory) is implementing the internal SPI realm-restapi-extension
```

Or check in Admin Console:
1. Navigate to: Admin Console → Server Info → Providers
2. Search for "realm-restapi-extension"
3. You should see "mfa" in the list

---

## 🧪 Testing

### Manual Testing with cURL

**1. Get Admin Token:**
```bash
ADMIN_TOKEN=$(curl -s -X POST \
  http://localhost:9002/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=admin123" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')
```

**2. Enroll User:**
```bash
curl -X POST \
  http://localhost:9002/realms/kal-sense/mfa/enroll \
  -H 'Content-Type: application/json' \
  -d '{"userId": "USER_KEYCLOAK_UUID"}'
```

**3. Verify OTP:**
```bash
curl -X POST \
  http://localhost:9002/realms/kal-sense/mfa/verify \
  -H 'Content-Type: application/json' \
  -d '{"userId": "USER_KEYCLOAK_UUID", "otp": "123456"}'
```

**4. Remove TOTP:**
```bash
curl -X DELETE \
  http://localhost:9002/realms/kal-sense/mfa/remove \
  -H 'Content-Type: application/json' \
  -d '{"userId": "USER_KEYCLOAK_UUID"}'
```

---

## 🔒 Security Considerations

### Authentication

- Endpoints are called from the **API Gateway** using admin privileges
- Users never call these endpoints directly
- The API Gateway validates user credentials before calling MFA endpoints

### Secret Storage

- TOTP secrets are stored securely in Keycloak's database
- Secrets are **Base32-encoded** as per RFC 4648
- Pending secrets (during enrollment) are stored in-memory and cleared after successful verification

### OTP Validation

- **Time window: 3 periods** (~90 seconds validity)
- Prevents replay attacks (Keycloak tracks used codes)
- Uses SHA-1 HMAC algorithm (standard for TOTP)

### Rate Limiting

- Implement rate limiting at the API Gateway level
- Recommended: 5 attempts per user per 5 minutes
- Keycloak's built-in brute force detection also applies

---

## 🐛 Troubleshooting

### Endpoint returns 404

**Cause:** Provider not loaded or incorrect URL

**Solution:**
1. Verify JAR is in `/opt/keycloak/providers/`
2. Check Docker logs: `docker logs backend_keycloak | grep mfa`
3. Ensure you ran `kc.sh build` (happens automatically in Dockerfile)
4. Verify realm name in URL matches your Keycloak realm

### QR code returns null

**Cause:** QR code generation failed

**Solution:**
1. Check Keycloak logs for errors
2. Verify ZXing library is included (bundled in JAR)
3. Ensure userId is valid Keycloak UUID (not username)

### OTP verification always fails

**Causes:**
1. User scanned an old QR code
2. Time drift between server and client
3. User entered expired code (>90 seconds old)

**Solutions:**
1. Generate fresh QR code and scan again
2. Sync server time with NTP: `ntpdate -s time.nist.gov`
3. Ask user to enter code immediately after it appears
4. Check logs for "OTP validation result" messages

### "No pending secret or existing credential found"

**Cause:** User called `/mfa/verify` without calling `/mfa/enroll` first (during initial setup)

**Solution:**
1. Call `/mfa/enroll` first to generate secret
2. Then call `/mfa/verify` with OTP code
3. For existing users, this shouldn't happen (credential is stored)

### Maven build fails

**Cause:** Missing dependencies or wrong Java version

**Solution:**
```bash
# Check Java version (needs 17+)
java -version

# Clean and rebuild
mvn clean install -U

# Skip tests if needed
mvn clean package -DskipTests
```

---

## 📊 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Kal-Sense Frontend                       │
│                      (React App)                             │
└────────────────────────┬─────────────────────────────────────┘
                         │ /login (username + password + otp)
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                     API Gateway (Python)                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Login Flow:                                           │  │
│  │  1. Check if user has OTP configured                   │  │
│  │  2. Verify OTP via Keycloak MFA endpoint               │  │
│  │  3. Get token via Keycloak Admin impersonation         │  │
│  └────────────────────┬───────────────────────────────────┘  │
└───────────────────────┼──────────────────────────────────────┘
                        │ POST /mfa/verify
                        │ POST /mfa/enroll
                        │ DELETE /mfa/remove
                        ↓
┌──────────────────────────────────────────────────────────────┐
│                     Keycloak (26.3.3)                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │        MFA Provider (Custom SPI)                       │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  MfaResourceProvider                             │  │  │
│  │  │  - Registers REST endpoints                      │  │  │
│  │  └──────────────────┬───────────────────────────────┘  │  │
│  │                     │                                   │  │
│  │  ┌──────────────────▼───────────────────────────────┐  │  │
│  │  │  TotpResource                                    │  │  │
│  │  │  - /enroll  (Generate secret + QR)               │  │  │
│  │  │  - /verify  (Verify OTP + save credential)       │  │  │
│  │  │  - /remove  (Delete credential)                  │  │  │
│  │  └──────────────────┬───────────────────────────────┘  │  │
│  │                     │                                   │  │
│  │  ┌──────────────────▼───────────────────────────────┐  │  │
│  │  │  TotpManager                                     │  │  │
│  │  │  - Generate Base32 secrets                       │  │  │
│  │  │  - Create QR codes (ZXing)                       │  │  │
│  │  │  - Verify TOTP codes (Keycloak TimeBasedOTP)    │  │  │
│  │  │  - Manage credentials (Keycloak CredentialMgr)  │  │  │
│  │  └──────────────────┬───────────────────────────────┘  │  │
│  └────────────────────┼────────────────────────────────────┘  │
│                       │                                       │
│  ┌────────────────────▼────────────────────────────────────┐  │
│  │         Keycloak Credential Manager                     │  │
│  │         (Built-in OTP Credential Storage)               │  │
│  └────────────────────┬────────────────────────────────────┘  │
│                       │                                       │
│  ┌────────────────────▼────────────────────────────────────┐  │
│  │              PostgreSQL Database                        │  │
│  │              (User Credentials Storage)                 │  │
│  └─────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 📦 Dependencies

Managed by Maven in `pom.xml`:

- **Keycloak Core** (26.3.3) - Base Keycloak functionality
- **ZXing Core & JavaSE** (3.5.2) - QR code generation
- **Keycloak Services** (26.3.3) - SPI interfaces
- **RESTEasy Reactive** (6.2.7.Final) - JAX-RS implementation
- **JBoss Logging** - Logging framework

All dependencies are bundled in the fat JAR via Maven Shade Plugin.

---

## 🔄 Migration from Existing Keycloak

If upgrading from a Keycloak instance without this extension:

### Data Safety

✅ **All user data is preserved** - stored in PostgreSQL database
✅ **Existing users unaffected** - MFA is opt-in
✅ **No breaking changes** - just adds new endpoints

### Migration Steps

1. **Backup database:**
   ```bash
   docker exec backend_keycloak_db pg_dump -U keycloak keycloak > backup.sql
   ```

2. **Build new Keycloak image:**
   ```bash
   cd keycloak_extensions/mfa-provider && mvn clean package
   cd ../.. && docker-compose -f docker-compose.minimal.yml build keycloak
   ```

3. **Stop old Keycloak:**
   ```bash
   docker-compose -f docker-compose.minimal.yml stop keycloak
   ```

4. **Start new Keycloak:**
   ```bash
   docker-compose -f docker-compose.minimal.yml up -d keycloak
   ```

5. **Verify:**
   ```bash
   docker logs backend_keycloak | grep "mfa"
   ```

**Rollback:** If issues occur, restore from backup and redeploy old image.

---

## 📚 References

- [RFC 6238 - TOTP: Time-Based One-Time Password Algorithm](https://tools.ietf.org/html/rfc6238)
- [RFC 4226 - HOTP: HMAC-Based One-Time Password Algorithm](https://tools.ietf.org/html/rfc4226)
- [RFC 4648 - Base32 Encoding](https://tools.ietf.org/html/rfc4648)
- [Keycloak SPI Documentation](https://www.keycloak.org/docs/latest/server_development/)
- [Google Authenticator Key URI Format](https://github.com/google/google-authenticator/wiki/Key-Uri-Format)
- [ZXing (Zebra Crossing) Library](https://github.com/zxing/zxing)

---

## 📄 License

Same as parent project (Kal-Sense).

---

## 🤝 Support

For issues or questions:
1. Check troubleshooting section above
2. Review Keycloak logs: `docker logs backend_keycloak`
3. Contact the Kal-Sense development team
