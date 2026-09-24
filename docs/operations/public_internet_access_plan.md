# UVU Autograder — Public Internet Access & IT Coordination Specification

This document provides the formal architecture specification for UVU Academic IT, Network Operations, and Identity Services to enable secure public internet access for the **UVU Autograder** on the dedicated Dell workstation host.

---

## 1. Executive Summary & Host Context

- **Host Identity:** Dell Pro Max Tower T2 (Ubuntu 24.04.5 LTS, 32GB RAM, NVIDIA RTX PRO 4500)
- **Campus LAN IP:** `10.115.20.200` (static)
- **Proposed Public FQDN:** `autograder.cs.uvu.edu`
- **Application Role:** Academic Python autograding platform serving students (unauthenticated sandbox) and computer science faculty/TAs (Microsoft Entra ID authenticated staff portal).

---

## 2. Ingress & Port Layout

The autograder stack strictly enforces defense-in-depth network boundaries. All internal microservices (databases, execution sandboxes, brokers, and web processes) are bound to `127.0.0.1` and are never directly routable from outside the host.

### External Firewall Rules Required (UVU IT)
| Port | Protocol | Source | Destination | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `80` | TCP | `0.0.0.0/0` | `10.115.20.200:80` | HTTP Ingress (Redirects permanently 301 $\to$ HTTPS `443`) |
| `443` | TCP | `0.0.0.0/0` | `10.115.20.200:443` | HTTPS Ingress (Nginx TLS termination) |
| `22` | TCP | Campus Subnets / VPN (`campusvpn.uvu.edu`) | `10.115.20.200:22` | Administrative SSH access for operator maintenance |

### Internal Host Bindings (Isolated to `127.0.0.1`)
| Port | Service | Bound Interface | External Access |
| :--- | :--- | :--- | :--- |
| `3000` | Next.js Frontend Server | `127.0.0.1:3000` | **Blocked** (reverse proxied via Nginx) |
| `8000` | FastAPI Backend Container | `127.0.0.1:8000` | **Blocked** (reverse proxied via Nginx) |
| `5432` | PostgreSQL 16 Container | `127.0.0.1:5432` | **Blocked** (no external routing) |
| `6379` | Redis 7 Broker Container | `127.0.0.1:6379` | **Blocked** (no external routing) |
| `2358` | Judge0 Execution CE Sandbox | `127.0.0.1:2358` | **Blocked** (no external routing) |

---

## 3. Ingress Architecture Options

### Option A: Direct Host TLS Termination (Recommended)
UVU IT assigns public DNS A-record `autograder.cs.uvu.edu` $\to$ public NAT IP $\to$ forwards ports 80/443 to `10.115.20.200`. Nginx on the workstation terminates TLS using institutional certificates (e.g., InCommon / Sectigo wildcard `*.cs.uvu.edu`).

#### Workstation Nginx Configuration (`/etc/nginx/sites-available/autograder.conf`):
```nginx
# 1. HTTP -> HTTPS Permanent Redirect
server {
    listen 80;
    listen [::]:80;
    server_name autograder.cs.uvu.edu;

    return 301 https://$host$request_uri;
}

# 2. HTTPS Production Reverse Proxy
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name autograder.cs.uvu.edu;

    # Institutional TLS Certificates
    ssl_certificate /etc/ssl/certs/autograder_cs_uvu_edu.crt;
    ssl_certificate_key /etc/ssl/private/autograder_cs_uvu_edu.key;

    # Mozilla Intermediate TLS Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Maximum bundle upload size (matches application 50MB limit)
    client_max_body_size 52M;

    # Backend API Routing
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    # API Health Probe
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
    }

    # Next.js Frontend Routing
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

### Option B: Upstream Institutional Reverse Proxy / WAF
If UVU IT utilizes a centralized reverse proxy (e.g., F5 BIG-IP, Cloudflare Enterprise, AWS ALB), TLS can terminate upstream. The upstream proxy must:
1. Forward clean HTTP traffic to `10.115.20.200:80`.
2. Pass header `X-Forwarded-Proto: https`.
3. Support request bodies up to `52MB` for zip uploads.
4. Support HTTP/1.1 WebSocket upgrade for live terminal streaming.

### Post-Ingress Verification
After DNS and ingress routing are in place, operators and IT engineers can verify end-to-end functionality using the automated smoke test suite:
```bash
# Verify all endpoints through the institutional domain or public reverse proxy
bash scripts/smoke_test.sh autograder.cs.uvu.edu

# Or from remote administrative workstations (PowerShell):
pwsh -File scripts/smoke_test.ps1 -TargetHost autograder.cs.uvu.edu
```

---

## 4. Microsoft Entra ID App Registration Handover

To enable institutional single sign-on for faculty and TAs, the Azure AD App Registration in the UVU Microsoft tenant requires the following redirect URI:

- **Application (client) ID:** *(Provided by UVU IT)*
- **Directory (tenant) ID:** *(UVU Institutional Tenant ID)*
- **Authentication Type:** Web Application + Single Page Application (PKCE)
- **Configured Redirect URIs:**
  - `https://autograder.cs.uvu.edu/api/auth/microsoft/callback` (Production)
  - `http://localhost:3000/api/auth/microsoft/callback` (Local Development)
- **Required Token Claims:**
  - `email` or `preferred_username` (must end with `@uvu.edu`)
  - `oid` (Azure Object ID, used for immutable identity binding)
  - `name` (Display name)
- **Token Verification:** The backend verifies incoming ID tokens directly against Microsoft's public OpenID JWKS (`https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys`). No client secret is stored in student browser sessions.
- **Pre-Flight Verification:** Operators can execute `python3 scripts/verify_entra_id_config.py --env-file .env` on the host to validate network reachability to Microsoft discovery endpoints, verify public JWKS retrieval, and confirm configuration readiness before going live.

---

## 5. Security & FERPA Posture

1. **Ephemeral Sandboxing:** Untrusted student Python submissions execute inside Kata Containers (hardware virtualization via QEMU/KVM) with no host filesystem access, no network access, and strict cgroup CPU/memory caps.
2. **Strict ≤24-Hour Retention:** Student submission files and review workspaces are physically unlinked and purged from host disk within 24 hours of batch upload by an independent systemd cleanup worker.
3. **Restricted Staff Access:** Unprovisioned UVU accounts signing in via Microsoft Entra ID receive `403 Forbidden` unless pre-provisioned by an administrator.
