package com.authgateway.keycloak.mfa;

import com.authgateway.keycloak.mfa.models.EnrollmentRequest;
import com.authgateway.keycloak.mfa.models.EnrollmentResponse;
import com.authgateway.keycloak.mfa.models.VerifyRequest;
import com.authgateway.keycloak.mfa.models.VerifyResponse;
import com.authgateway.keycloak.mfa.models.RemoveRequest;
import com.authgateway.keycloak.mfa.models.RemoveResponse;
import com.authgateway.keycloak.mfa.utils.TotpManager;
import org.jboss.logging.Logger;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.RealmModel;
import org.keycloak.models.UserModel;
import org.keycloak.models.credential.OTPCredentialModel;
import org.keycloak.credential.CredentialProvider;
import org.keycloak.credential.OTPCredentialProvider;

import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

/**
 * REST Resource for TOTP/2FA operations.
 * Accessible at: /realms/{realm}/mfa/totp/*
 */
@Path("/totp")
public class TotpResource {

    private static final Logger logger = Logger.getLogger(TotpResource.class);
    private final KeycloakSession session;

    public TotpResource(KeycloakSession session) {
        this.session = session;
    }

    /**
     * Enroll a user in TOTP/2FA.
     * Generates a secret and returns QR code data.
     * 
     * POST /realms/{realm}/mfa/totp/enroll
     */
    @POST
    @Path("/enroll")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response enroll(EnrollmentRequest request) {
        try {
            logger.infof("TOTP enrollment request for user: %s", request.getUserId());

            // Validate request
            if (request.getUserId() == null || request.getUserId().isEmpty()) {
                return Response.status(Response.Status.BAD_REQUEST)
                    .entity(new ErrorResponse("userId is required"))
                    .build();
            }

            // Get realm and user
            RealmModel realm = session.getContext().getRealm();
            UserModel user = findUser(realm, request.getUserId());
            
            if (user == null) {
                logger.warnf("User not found: %s", request.getUserId());
                return Response.status(Response.Status.NOT_FOUND)
                    .entity(new ErrorResponse("User not found"))
                    .build();
            }

            // Generate TOTP secret and QR code
            TotpManager totpManager = new TotpManager(session, realm);
            EnrollmentResponse response = totpManager.generateTotpSecret(user);

            logger.infof("TOTP secret generated for user: %s", user.getUsername());
            
            return Response.ok(response).build();

        } catch (Exception e) {
            logger.errorf(e, "Error enrolling user in TOTP: %s", request.getUserId());
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(new ErrorResponse("Failed to enroll user: " + e.getMessage()))
                .build();
        }
    }

    /**
     * Verify OTP code and complete enrollment.
     * 
     * POST /realms/{realm}/mfa/totp/verify
     */
    @POST
    @Path("/verify")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response verify(VerifyRequest request) {
        try {
            logger.infof("TOTP verification request for user: %s", request.getUserId());

            // Validate request
            if (request.getUserId() == null || request.getUserId().isEmpty()) {
                return Response.status(Response.Status.BAD_REQUEST)
                    .entity(new ErrorResponse("userId is required"))
                    .build();
            }
            if (request.getOtp() == null || request.getOtp().isEmpty()) {
                return Response.status(Response.Status.BAD_REQUEST)
                    .entity(new ErrorResponse("otp is required"))
                    .build();
            }

            // Get realm and user
            RealmModel realm = session.getContext().getRealm();
            UserModel user = findUser(realm, request.getUserId());
            
            if (user == null) {
                return Response.status(Response.Status.NOT_FOUND)
                    .entity(new ErrorResponse("User not found"))
                    .build();
            }

            // Verify OTP and save credential
            TotpManager totpManager = new TotpManager(session, realm);
            boolean verified = totpManager.verifyAndSaveOtp(user, request.getOtp());

            if (verified) {
                logger.infof("TOTP verified and saved for user: %s", user.getUsername());
                return Response.ok(new VerifyResponse(true, "OTP verified and credential saved successfully")).build();
            } else {
                logger.warnf("Invalid OTP for user: %s", user.getUsername());
                return Response.status(Response.Status.BAD_REQUEST)
                    .entity(new VerifyResponse(false, "Invalid OTP code"))
                    .build();
            }

        } catch (Exception e) {
            logger.errorf(e, "Error verifying OTP for user: %s", request.getUserId());
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(new ErrorResponse("Failed to verify OTP: " + e.getMessage()))
                .build();
        }
    }

    /**
     * Remove TOTP credential from user.
     * 
     * DELETE /realms/{realm}/mfa/totp/remove
     */
    @DELETE
    @Path("/remove")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response remove(RemoveRequest request) {
        try {
            logger.infof("TOTP removal request for user: %s", request.getUserId());

            // Validate request
            if (request.getUserId() == null || request.getUserId().isEmpty()) {
                return Response.status(Response.Status.BAD_REQUEST)
                    .entity(new ErrorResponse("userId is required"))
                    .build();
            }

            // Get realm and user
            RealmModel realm = session.getContext().getRealm();
            UserModel user = findUser(realm, request.getUserId());
            
            if (user == null) {
                return Response.status(Response.Status.NOT_FOUND)
                    .entity(new ErrorResponse("User not found"))
                    .build();
            }

            // Remove TOTP credential
            TotpManager totpManager = new TotpManager(session, realm);
            boolean removed = totpManager.removeTotpCredential(user);

            if (removed) {
                logger.infof("TOTP credential removed for user: %s", user.getUsername());
                return Response.ok(new RemoveResponse(true, "TOTP credential removed successfully")).build();
            } else {
                return Response.status(Response.Status.NOT_FOUND)
                    .entity(new RemoveResponse(false, "No TOTP credential found"))
                    .build();
            }

        } catch (Exception e) {
            logger.errorf(e, "Error removing TOTP for user: %s", request.getUserId());
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(new ErrorResponse("Failed to remove TOTP: " + e.getMessage()))
                .build();
        }
    }

    /**
     * Find user by ID or username
     */
    private UserModel findUser(RealmModel realm, String userIdOrUsername) {
        // Try as UUID first
        UserModel user = session.users().getUserById(realm, userIdOrUsername);
        
        // If not found, try as username
        if (user == null) {
            user = session.users().getUserByUsername(realm, userIdOrUsername);
        }
        
        return user;
    }

    /**
     * Error response model
     */
    public static class ErrorResponse {
        private String error;

        public ErrorResponse(String error) {
            this.error = error;
        }

        public String getError() {
            return error;
        }

        public void setError(String error) {
            this.error = error;
        }
    }
}
