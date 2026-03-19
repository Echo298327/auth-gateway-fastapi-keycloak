# Security Policy

## Reporting a Vulnerability
I take security seriously and am always happy to address any issues you discover. If you find a security vulnerability in this project, please report it responsibly. I am committed to working with the community to resolve security issues quickly.

### How to Report
- **Contact me:** Send an email to **[shalomber17@gmail.com]** with details of the vulnerability.  
- **Include:**  
  - A clear description of the vulnerability.  
  - Steps to reproduce the issue.  
  - Potential impact or risk.  
  - Any suggested fixes (if applicable).  

I kindly ask that you do not publicly disclose the vulnerability until I have confirmed it and released a fix.

## Current Security Features
This project implements the following security mechanisms:

- **Keycloak Integration:**  
  - Middleware validates tokens for authentication and enforces role-based access control.
  - Secure token handling and user entitlement checks are implemented.

- **Security Headers:**  
  The Gateway service includes a `SecurityHeadersMiddleware` (`gateway/src/middleware/security_headers.py`) that adds the following headers to every response:
  - `X-Content-Type-Options: nosniff` — prevents MIME-type sniffing
  - `X-XSS-Protection: 1; mode=block` — enables browser XSS filter
  - `Referrer-Policy: strict-origin-when-cross-origin` — limits referrer info leakage
  - `Permissions-Policy: camera=(), geolocation=(), microphone=()` — disables sensitive browser APIs
  - `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'` — blocks resource loading and iframe embedding
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains` — forces HTTPS (production only, skipped when `ENVIRONMENT=local`)

- **CORS:**  
  - Configurable via the `CORS_ORIGINS` environment variable (comma-separated list of allowed origins). Defaults to `*` for local development.

- **Environment Variables:**  
  - Sensitive data, like credentials and keys, are managed through environment variables.
  - `.env` and `.env.docker` are excluded from version control via `.gitignore`. Use the provided `.env.example` and `.env.docker.example` files as templates.

- **Docker Compose Setup:**  
  - The `docker-compose.yml` file is configured for local development. For production, ensure secure configurations, such as enabling HTTPS with a reverse proxy.

## Recommendations for Users
- **Do not commit `.env` files to GitHub**, especially if they contain sensitive information like credentials, connection strings, or API keys.  
  - `.env` and `.env.docker` are already in `.gitignore`. Use the `.example` files as templates.  
- Always use HTTPS in production to secure communication.
- Regularly review and update the environment variables used in your setup.
- Follow best practices for securing your Keycloak server and managing its credentials.

## Acknowledgments
I appreciate contributions and feedback from the community to help improve this project’s security. Thank you for helping maintain a secure environment for all users.
