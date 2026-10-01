# Nginx deployment assets

- [autograder-http.conf](autograder-http.conf): LAN/staging HTTP template.
- [autograder-tls.conf](autograder-tls.conf): institutional TLS template and HTTP redirect.

Follow the [workstation guide](../../docs/guides/workstation.md#build-and-start-the-frontend-and-proxy) for installation, certificates, identity routing and endpoint checks. These assets currently intercept Next.js `/api/auth/microsoft/*` with their general FastAPI `/api/` location; resolve and test that conflict before relying on proxy-based Microsoft sign-in.

Edit reviewed configuration in these assets rather than maintaining a second pasted Nginx configuration in docs. Validate the installed file with `nginx -t` before reload.
