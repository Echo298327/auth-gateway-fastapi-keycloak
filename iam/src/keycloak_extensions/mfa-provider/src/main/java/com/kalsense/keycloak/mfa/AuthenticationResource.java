package com.kalsense.keycloak.mfa;

import com.kalsense.keycloak.mfa.models.ErrorResponse;
import com.kalsense.keycloak.mfa.models.ValidatePasswordRequest;
import com.kalsense.keycloak.mfa.models.ValidatePasswordResponse;
import org.jboss.logging.Logger;
import org.keycloak.models.*;

import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

/**
 * REST Resource for password validation before MFA.
 * Accessible at: /realms/{realm}/mfa/auth/*
 * 
 * Purpose: Validate username and password BEFORE asking for OTP,
 * so users with wrong passwords don't get sent to OTP screen.
 */
@Path("/auth")
public class AuthenticationResource {

    private static final Logger logger = Logger.getLogger(AuthenticationResource.class);
    private final KeycloakSession session;

    public AuthenticationResource(KeycloakSession session) {
        this.session = session;
    }

    /**
     * Validate username and password only (no OTP check).
     * 
     * POST /realms/{realm}/mfa/auth/validate
     * 
     * SECURITY: Returns only valid=true/false to prevent account enumeration.
     * Does NOT reveal whether username or password was incorrect.
     * 
     * Returns:
     * - valid: true - Credentials are correct, can proceed to MFA check
     * - valid: false - Credentials are incorrect (doesn't specify which part)
     * 
     * Backend can then:
     * - If valid=true: Check MFA status and ask for OTP if needed
     * - If valid=false: Return generic error, stay on login screen
     */
    @POST
    @Path("/validate")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response validatePassword(ValidatePasswordRequest request) {
        try {
            logger.infof("Password validation request for username: %s", request.getUsername());

            // Validate request
            if (request.getUsername() == null || request.getUsername().isEmpty()) {
                return Response.status(Response.Status.BAD_REQUEST)
                    .entity(new ErrorResponse("Username is required"))
                    .build();
            }

            if (request.getPassword() == null || request.getPassword().isEmpty()) {
                return Response.status(Response.Status.BAD_REQUEST)
                    .entity(new ErrorResponse("Password is required"))
                    .build();
            }

            // Get realm
            RealmModel realm = session.getContext().getRealm();
            if (realm == null) {
                logger.error("Realm not found in session context");
                return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity(new ErrorResponse("Realm configuration error"))
                    .build();
            }

            // Step 1: Check if user exists
            UserModel user = session.users().getUserByUsername(realm, request.getUsername());
            if (user == null) {
                // Also try email
                user = session.users().getUserByEmail(realm, request.getUsername());
            }

            if (user == null) {
                // SECURITY: Don't reveal that user doesn't exist
                logger.warnf("User not found: %s", request.getUsername());
                return Response.ok()
                    .entity(new ValidatePasswordResponse(false))
                    .build();
            }

            // Step 2: Validate password
            boolean passwordValid = user.credentialManager()
                .isValid(UserCredentialModel.password(request.getPassword()));

            if (!passwordValid) {
                // SECURITY: Generic response, doesn't reveal password was wrong
                logger.warnf("Invalid password for user: %s", user.getUsername());
                return Response.ok()
                    .entity(new ValidatePasswordResponse(false))
                    .build();
            }

            // Password is valid!
            logger.infof("Password validated for user: %s", user.getUsername());
            return Response.ok()
                .entity(new ValidatePasswordResponse(true))
                .build();

        } catch (Exception e) {
            logger.errorf(e, "Error during password validation for user: %s", request.getUsername());
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(new ErrorResponse("Validation error: " + e.getMessage()))
                .build();
        }
    }
}
