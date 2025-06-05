---
name: Bug report
about: Create a report to help us improve
title: BUG
labels: bug
assignees: Echo298327

---

**Describe the bug**  
A clear and concise description of the issue you're encountering in the backend service (e.g., incorrect status code, token validation failure, unexpected exception, etc.).

---

**To Reproduce**  
Steps to reproduce the behavior. Include any relevant request examples:

1. Endpoint called: `POST /auth/login`
2. Request payload:
   ```json
   {
     "username": "example_user",
     "password": "invalid_pass"
   }
