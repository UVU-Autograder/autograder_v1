# Nginx Reverse Proxy Configurations

This directory contains the production and staging reverse proxy configurations for the UVU Autograder host deployment.

---

## Configurations

| File | Purpose | Ports |
| :--- | :--- | :--- |
| `autograder-http.conf` | On-prem LAN / staging reverse proxy before TLS issuance | `80` (HTTP) |
| `autograder-tls.conf` | Institutional production deployment with TLS termination | `80` (HTTP $\to$ HTTPS redirect), `443` (HTTPS) |

---

## Routing Contracts

- **`/api/*`**: Strips `/api` prefix and proxies to FastAPI backend (`http://127.0.0.1:8000/`).
- **`/health` & `/openapi.json`**: Proxied directly to FastAPI backend (`http://127.0.0.1:8000`).
- **`/` and all frontend routes**: Proxied to Next.js production server (`http://127.0.0.1:3000`).
- **`client_max_body_size 52M`**: Accommodates 50MB ZIP bundle upload contract plus multipart form-data overhead.

---

## Workstation Installation

### For Local / LAN HTTP Deployment (Port 80):

```bash
sudo cp scripts/nginx/autograder-http.conf /etc/nginx/sites-available/autograder.conf
sudo ln -sf /etc/nginx/sites-available/autograder.conf /etc/nginx/sites-enabled/autograder.conf
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### For Institutional TLS Deployment (Port 443):

Once UVU IT issues the SSL certificate and private key:

```bash
# 1. Place certificates in standard secure directories
sudo cp autograder_cs_uvu_edu.crt /etc/ssl/certs/autograder_cs_uvu_edu.crt
sudo cp autograder_cs_uvu_edu.key /etc/ssl/private/autograder_cs_uvu_edu.key
sudo chmod 600 /etc/ssl/private/autograder_cs_uvu_edu.key

# 2. Deploy TLS configuration
sudo cp scripts/nginx/autograder-tls.conf /etc/nginx/sites-available/autograder.conf
sudo ln -sf /etc/nginx/sites-available/autograder.conf /etc/nginx/sites-enabled/autograder.conf
sudo nginx -t
sudo systemctl reload nginx
```
