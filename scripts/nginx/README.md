# Nginx deployment assets

- [autograder-http.conf](autograder-http.conf): LAN/staging HTTP template.
- [autograder-tls.conf](autograder-tls.conf): institutional TLS template and HTTP redirect.

Follow the [workstation guide](../../docs/guides/workstation.md#build-and-start-the-frontend-and-proxy) for installation, certificates, identity routing and endpoint checks. These assets implement longest-prefix routing (`location /api/auth/microsoft/`) to proxy Microsoft Entra OAuth initiation and callbacks directly to Next.js (`http://127.0.0.1:3000`) ahead of the general FastAPI `location /api/` proxy (`http://127.0.0.1:8000/`).

Edit reviewed configuration in these assets rather than maintaining a second pasted Nginx configuration in docs. Validate the installed file with `nginx -t` before reload.
