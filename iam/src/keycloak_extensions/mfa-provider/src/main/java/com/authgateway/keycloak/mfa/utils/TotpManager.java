package com.authgateway.keycloak.mfa.utils;

import com.google.zxing.BarcodeFormat;
import com.google.zxing.EncodeHintType;
import com.google.zxing.WriterException;
import com.google.zxing.client.j2se.MatrixToImageWriter;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import com.authgateway.keycloak.mfa.models.EnrollmentResponse;
import org.jboss.logging.Logger;
import org.keycloak.credential.CredentialModel;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.RealmModel;
import org.keycloak.models.UserModel;
import org.keycloak.models.credential.OTPCredentialModel;
import org.keycloak.models.utils.HmacOTP;
import org.keycloak.models.utils.TimeBasedOTP;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.security.SecureRandom;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Base64;

/**
 * Utility class for managing TOTP operations.
 */
public class TotpManager {

    private static final Logger logger = Logger.getLogger(TotpManager.class);
    
    private final KeycloakSession session;
    private final RealmModel realm;
    
    // Default TOTP settings
    private static final int SECRET_LENGTH = 20; // 160 bits
    private static final int QR_CODE_SIZE = 300;
    private static final String DEFAULT_ALGORITHM = "HmacSHA1";
    private static final int DEFAULT_DIGITS = 6;
    private static final int DEFAULT_PERIOD = 30;
    
    // Temporary storage for secrets during enrollment
    // In production, consider using a cache or database
    private static final Map<String, String> pendingSecrets = new HashMap<>();

    public TotpManager(KeycloakSession session, RealmModel realm) {
        this.session = session;
        this.realm = realm;
    }

    /**
     * Generate TOTP secret and QR code for a user.
     * If a pending secret already exists for this user, reuse it.
     */
    public EnrollmentResponse generateTotpSecret(UserModel user) throws WriterException, IOException {
        // Check if we already have a pending secret for this user
        String secret = pendingSecrets.get(user.getId());
        
        if (secret == null) {
            // No pending secret - generate a new one
            secret = generateSecret();
            logger.infof("Generated NEW secret for user: %s", user.getUsername());
        } else {
            // Reuse existing pending secret
            logger.infof("Reusing EXISTING pending secret for user: %s", user.getUsername());
        }
        
        // Store/update in pending secrets
        pendingSecrets.put(user.getId(), secret);
        
        // Get realm settings
        String issuer = realm.getName();
        String accountName = user.getUsername();
        
        // Build otpauth URL
        String otpauthUrl = buildOtpauthUrl(issuer, accountName, secret);
        
        // Generate QR code
        String qrCodeDataUrl = generateQrCode(otpauthUrl);
        
        // Build response
        EnrollmentResponse response = new EnrollmentResponse();
        response.setSecret(secret);
        response.setOtpauthUrl(otpauthUrl);
        response.setQrCodeDataUrl(qrCodeDataUrl);
        response.setIssuer(issuer);
        response.setPeriod(DEFAULT_PERIOD);
        response.setDigits(DEFAULT_DIGITS);
        response.setAlgorithm(DEFAULT_ALGORITHM);
        
        return response;
    }

    /**
     * Verify OTP code and save credential if valid.
     */
    public boolean verifyAndSaveOtp(UserModel user, String otpCode) {
        // First check if user already has OTP configured (for subsequent logins)
        List<CredentialModel> credentials = user.credentialManager()
            .getStoredCredentialsByTypeStream(OTPCredentialModel.TYPE)
            .toList();
        
        if (!credentials.isEmpty()) {
            // User already has OTP configured - verify against stored credential
                logger.infof("User %s has existing OTP credential, verifying against stored credential", user.getUsername());
                CredentialModel credential = credentials.get(0);
                
                try {
                    OTPCredentialModel otpCredential = OTPCredentialModel.createFromCredentialModel(credential);
                    String storedSecret = otpCredential.getOTPSecretData().getValue();
                
                TimeBasedOTP totp = new TimeBasedOTP(DEFAULT_ALGORITHM, DEFAULT_DIGITS, DEFAULT_PERIOD, 3);
                byte[] secretBytes = base32Decode(storedSecret);
                boolean valid = totp.validateTOTP(otpCode, secretBytes);
                
                logger.infof("OTP validation result for user %s: %s", user.getUsername(), valid);
                return valid;
            } catch (Exception e) {
                logger.errorf("Error verifying existing OTP credential for user %s: %s", user.getUsername(), e.getMessage());
                return false;
            }
        }
        
        // No existing credential - check pending secrets (for initial setup)
        String secret = pendingSecrets.get(user.getId());
        
        if (secret == null) {
            logger.warnf("No pending secret or existing credential found for user: %s", user.getUsername());
            return false;
        }
        
        logger.infof("Verifying OTP for user %s during initial setup", user.getUsername());
        
        // Verify the OTP code
        TimeBasedOTP totp = new TimeBasedOTP(DEFAULT_ALGORITHM, DEFAULT_DIGITS, DEFAULT_PERIOD, 3);
        
        // Decode the Base32-encoded secret before validation
        byte[] secretBytes = base32Decode(secret);
        boolean valid = totp.validateTOTP(otpCode, secretBytes);
        
        logger.infof("OTP validation result for user %s: %s", user.getUsername(), valid);
        
        if (valid) {
            // Save credential to Keycloak
            saveOtpCredential(user, secret);
            
            // Remove from pending
            pendingSecrets.remove(user.getId());
            
            logger.infof("OTP credential saved for user: %s", user.getUsername());
            return true;
        }
        
        logger.warnf("Invalid OTP code for user: %s", user.getUsername());
        return false;
    }

    /**
     * Remove TOTP credential from user.
     */
    public boolean removeTotpCredential(UserModel user) {
        List<CredentialModel> credentials = user.credentialManager()
            .getStoredCredentialsByTypeStream(OTPCredentialModel.TYPE)
            .toList();
        
        if (!credentials.isEmpty()) {
            for (CredentialModel credential : credentials) {
                user.credentialManager().removeStoredCredentialById(credential.getId());
            }
            
            // Also remove from pending if exists
            pendingSecrets.remove(user.getId());
            
            logger.infof("Removed %d TOTP credentials for user: %s", credentials.size(), user.getUsername());
            return true;
        }
        
        logger.warnf("No TOTP credentials found for user: %s", user.getUsername());
        return false;
    }

    /**
     * Generate a random Base32-encoded secret.
     */
    private String generateSecret() {
        SecureRandom random = new SecureRandom();
        byte[] bytes = new byte[SECRET_LENGTH];
        random.nextBytes(bytes);
        return base32Encode(bytes);
    }
    
    /**
     * Base32 encoding implementation
     */
    private String base32Encode(byte[] data) {
        String alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
        StringBuilder result = new StringBuilder();
        int buffer = 0;
        int bitsLeft = 0;
        
        for (byte b : data) {
            buffer = (buffer << 8) | (b & 0xFF);
            bitsLeft += 8;
            
            while (bitsLeft >= 5) {
                result.append(alphabet.charAt((buffer >> (bitsLeft - 5)) & 0x1F));
                bitsLeft -= 5;
            }
        }
        
        if (bitsLeft > 0) {
            result.append(alphabet.charAt((buffer << (5 - bitsLeft)) & 0x1F));
        }
        
        return result.toString();
    }
    
    /**
     * Base32 decoding implementation
     */
    private byte[] base32Decode(String encoded) {
        String alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
        encoded = encoded.toUpperCase().replaceAll("=", "");
        
        ByteArrayOutputStream result = new ByteArrayOutputStream();
        int buffer = 0;
        int bitsLeft = 0;
        
        for (char c : encoded.toCharArray()) {
            int value = alphabet.indexOf(c);
            if (value == -1) {
                throw new IllegalArgumentException("Invalid Base32 character: " + c);
            }
            
            buffer = (buffer << 5) | value;
            bitsLeft += 5;
            
            if (bitsLeft >= 8) {
                result.write((buffer >> (bitsLeft - 8)) & 0xFF);
                bitsLeft -= 8;
            }
        }
        
        return result.toByteArray();
    }

    /**
     * Build otpauth:// URL for authenticator apps.
     */
    private String buildOtpauthUrl(String issuer, String accountName, String secret) {
        return String.format(
            "otpauth://totp/%s:%s?secret=%s&issuer=%s&digits=%d&period=%d&algorithm=%s",
            issuer,
            accountName,
            secret,
            issuer,
            DEFAULT_DIGITS,
            DEFAULT_PERIOD,
            "SHA1"
        );
    }

    /**
     * Generate QR code as Base64-encoded data URL.
     */
    private String generateQrCode(String text) throws WriterException, IOException {
        QRCodeWriter qrCodeWriter = new QRCodeWriter();
        
        Map<EncodeHintType, Object> hints = new HashMap<>();
        hints.put(EncodeHintType.CHARACTER_SET, "UTF-8");
        hints.put(EncodeHintType.MARGIN, 1);
        
        BitMatrix bitMatrix = qrCodeWriter.encode(text, BarcodeFormat.QR_CODE, QR_CODE_SIZE, QR_CODE_SIZE, hints);
        BufferedImage image = MatrixToImageWriter.toBufferedImage(bitMatrix);
        
        // Convert to Base64 data URL
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ImageIO.write(image, "PNG", baos);
        byte[] imageBytes = baos.toByteArray();
        String base64 = Base64.getEncoder().encodeToString(imageBytes);
        
        return "data:image/png;base64," + base64;
    }

    /**
     * Save OTP credential to user.
     */
    private void saveOtpCredential(UserModel user, String secret) {
        OTPCredentialModel credentialModel = OTPCredentialModel.createTOTP(
            secret,
            DEFAULT_DIGITS,
            DEFAULT_PERIOD,
            DEFAULT_ALGORITHM,
            "BASE32"
        );
        
        user.credentialManager().createStoredCredential(credentialModel);
    }
}
