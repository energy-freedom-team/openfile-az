# Self-hosting openfile-az

The openfile-az web app is a **static site** that runs entirely in the user's browser via [Pyodide](https://pyodide.org) (WebAssembly Python). There is no backend, no database, no server-side processing — so self-hosting means serving a folder of files over HTTP.

This document covers four deployment paths, ordered from easiest to most flexible:

- [Docker (one command)](#docker)
- [Python's built-in server (development / tiny deployments)](#python-http-server)
- [nginx / Caddy / Apache (production)](#nginx--caddy--apache)
- [Static hosting (Cloudflare Pages, GitHub Pages, Netlify, S3)](#static-hosting)

All four produce the same user experience. Pick whichever fits your infrastructure.

---

## Prerequisites

Before deploying, **build the web bundle once** from the repo root:

```bash
# Minimal build — Pyodide loads from CDN at first use
python3 web/scripts/build.py

# OR: fully-offline build — bundles Pyodide locally (~12MB extra)
python3 web/scripts/build.py --with-pyodide
```

This produces `web/dist/` containing:

```
web/dist/
├── index.html            UI
├── app.js, ui.js         browser app
├── styles.css
├── core.zip              openfile_az Python package
├── templates/            downloadable blank XLSX templates
├── vendor/pyodide/       (only with --with-pyodide)
└── build-info.json       version, git SHA, build timestamp
```

**Bundle Pyodide locally (`--with-pyodide`) if your users may be offline, are behind a corporate firewall that blocks `cdn.jsdelivr.net`, or if you want to guarantee the app keeps working even if the Pyodide CDN goes down.**

---

## Docker

The fastest way to run openfile-az on any server.

### From source

```bash
git clone https://github.com/energy-freedom-team/openfile-az
cd openfile-az
docker compose -f web/docker/docker-compose.yml up -d
```

Open [http://localhost:8080](http://localhost:8080).

To change the port:

```bash
OPENFILE_PORT=9000 docker compose -f web/docker/docker-compose.yml up -d
```

### From the published image

```bash
docker run -d \
  --name openfile-az \
  --read-only \
  --tmpfs /tmp --tmpfs /var/cache/nginx --tmpfs /var/run \
  --cap-drop ALL --cap-add NET_BIND_SERVICE \
  --security-opt no-new-privileges:true \
  -p 8080:80 \
  ghcr.io/energy-freedom-team/openfile-az:latest
```

### What's in the image

Two-stage build: a python:3.12-slim builder runs `build.py --with-pyodide`, then nginx:1.27-alpine serves `web/dist/`. The resulting image is ~30MB and serves only static files. It drops all Linux capabilities except `NET_BIND_SERVICE`, runs read-only with tmpfs mounts, and has no persistent storage.

---

## Python HTTP server

For quick local testing or very small deployments.

```bash
python3 web/scripts/build.py --with-pyodide
python3 web/scripts/serve.py              # http://127.0.0.1:8080
python3 web/scripts/serve.py --port 9000
python3 web/scripts/serve.py --host 0.0.0.0  # LAN-accessible
```

This is **not** production-grade (single-threaded, no HTTPS, no rate limiting) but it's perfect for running the tool on an air-gapped laptop or showing it on a projector during a committee meeting.

---

## nginx / Caddy / Apache

For public-facing production deployments on your own infrastructure.

### nginx

Copy `web/dist/` to your web root (e.g. `/var/www/openfile-az`), then:

```nginx
server {
    listen 443 ssl http2;
    server_name azfile.example.org;

    ssl_certificate     /etc/letsencrypt/live/azfile.example.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/azfile.example.org/privkey.pem;

    root /var/www/openfile-az;
    index index.html;

    # Pyodide-friendly isolation headers
    add_header Cross-Origin-Opener-Policy "same-origin" always;
    add_header Cross-Origin-Embedder-Policy "credentialless" always;

    # Security baseline
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "no-referrer" always;

    types {
        application/wasm wasm;
        text/javascript  js mjs;
    }

    gzip on;
    gzip_types text/plain text/css text/javascript application/javascript
               application/json application/wasm image/svg+xml;

    location /vendor/pyodide/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files $uri $uri/ =404;
    }
}
```

The complete `nginx.conf` used by the Docker image is at [`web/docker/nginx.conf`](docker/nginx.conf) — copy additional bits (CSP, cache rules) as desired.

### Caddy

```caddyfile
azfile.example.org {
    root * /var/www/openfile-az
    file_server

    header {
        Cross-Origin-Opener-Policy "same-origin"
        Cross-Origin-Embedder-Policy "credentialless"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "no-referrer"
    }

    @pyodide path /vendor/pyodide/*
    header @pyodide Cache-Control "public, immutable, max-age=31536000"

    encode gzip
}
```

### Apache

```apache
<VirtualHost *:443>
    ServerName azfile.example.org
    DocumentRoot /var/www/openfile-az

    Header set Cross-Origin-Opener-Policy "same-origin"
    Header set Cross-Origin-Embedder-Policy "credentialless"
    Header set X-Content-Type-Options "nosniff"

    AddType application/wasm .wasm
    AddType text/javascript .js .mjs

    <Directory /var/www/openfile-az>
        Options -Indexes +FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
</VirtualHost>
```

---

## Static hosting

openfile-az is a pure static site. Any static host works.

| Host | Steps |
|------|-------|
| **Cloudflare Pages** | `wrangler pages deploy web/dist` — or point a GitHub Action at the repo, build dir `web/dist`, build command `python3 web/scripts/build.py --with-pyodide` |
| **GitHub Pages** | Push `web/dist/` to a `gh-pages` branch, or use the [`actions/deploy-pages`](https://github.com/actions/deploy-pages) action |
| **Netlify** | Build command `python3 web/scripts/build.py --with-pyodide`, publish directory `web/dist` |
| **S3 + CloudFront** | `aws s3 sync web/dist s3://your-bucket/ --delete` then invalidate the distribution |
| **Vercel** | Same as Netlify — or drop `web/dist` in a Vercel project with "Other" framework preset |

Add custom headers matching the nginx config above (COOP / COEP / CSP) via your host's configuration. All of the above support setting response headers.

---

## Hardening

For a public deployment handling compliance-sensitive data:

1. **HTTPS only.** No exceptions. Use Let's Encrypt, Cloudflare, etc.
2. **HSTS.** Add `Strict-Transport-Security: max-age=31536000; includeSubDomains` after confirming the site works over HTTPS.
3. **Immutable Pyodide caching.** See `/vendor/pyodide/` config above — these assets are content-addressed by version, cache them forever.
4. **No server-side logging of URLs with query strings.** openfile-az never puts user data in URLs, but defense in depth: configure your web server's access log to omit query strings, or disable it entirely. You don't need access logs — there's no dynamic content.
5. **Minimal CSP.** The Docker image's CSP allows the Pyodide CDN as a fallback. If you built with `--with-pyodide`, tighten it:
   ```
   connect-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline';
   ```
   (`unsafe-eval` is required for WebAssembly instantiation in Pyodide; `unsafe-inline` is needed for Pyodide's internal bootstrapping. This is intrinsic to WASM-Python, not a lax config.)
6. **No analytics, no third-party tags.** Don't add them. The "your data never leaves your device" promise depends on it.
7. **Publish a verifiable build.** In your CI, compute and publish a SHA-256 hash of `web/dist/` so users can verify they're running the same bytes that the public build produced. Example:
   ```bash
   find web/dist -type f -exec sha256sum {} \; | sort > web/dist.sha256
   ```
8. **Keep forms **disabled** in CSP's `form-action`.** openfile-az has no forms that POST — everything is client-side.

---

## Updating

When a new openfile-az release lands:

```bash
git pull
python3 web/scripts/build.py --with-pyodide
# then: restart docker container, resync to static host, or refresh nginx root
```

Users get the new version on their next visit (hard refresh if heavily cached).

The AZ SOS periodically updates the underlying form. When that happens, openfile-az publishes a new version with updated field IDs. Pin to a version in your deployment pipeline if you need to amend prior filings using the old form.

---

## Verifying "no data leaves the browser"

You can — and should — independently verify this claim:

1. Open the hosted or self-hosted URL.
2. Open your browser's DevTools → Network tab.
3. Wait for the page to fully load (status bar shows "Ready").
4. **Disconnect from the internet** (wifi off, airplane mode, pull ethernet).
5. Load spreadsheets into the forms and click "Generate".
6. Watch the Network tab — no requests should fire.
7. The PDF download works anyway.

Verify the code: every file in this repo is MIT-licensed and on [GitHub](https://github.com/energy-freedom-team/openfile-az). There are no obfuscated minified bundles. `app.js` is 300 lines of human-readable JavaScript.

---

## Questions

File an issue: https://github.com/energy-freedom-team/openfile-az/issues
