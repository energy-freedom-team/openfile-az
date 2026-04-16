# openfile-az — self-hosted web container
# ---------------------------------------------------------------------------
# Two-stage build:
#   1. python slim: builds web/dist/ with Pyodide bundled locally
#   2. nginx alpine: serves the static bundle
# ---------------------------------------------------------------------------

FROM python:3.12-slim AS build

WORKDIR /src

# Install only what the build script needs (network access to download Pyodide)
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY openfile_az ./openfile_az
COPY examples ./examples
COPY web ./web

RUN python3 web/scripts/build.py --with-pyodide


# --- runtime stage ---------------------------------------------------------

FROM nginx:1.27-alpine

LABEL org.opencontainers.image.source="https://github.com/energy-freedom-team/openfile-az"
LABEL org.opencontainers.image.description="Arizona SOS Campaign Finance Report generator — self-hosted web UI"
LABEL org.opencontainers.image.licenses="MIT"

COPY --from=build /src/web/dist /usr/share/nginx/html
COPY web/docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --spider -q http://localhost/ || exit 1
