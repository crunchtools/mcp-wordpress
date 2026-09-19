# MCP WordPress CrunchTools Container
#
# Build:
#   podman build -t mcp-wordpress-crunchtools -f Containerfile .
#
# Setup (create upload directory on host before first run):
#   mkdir -p ~/.local/share/mcp-uploads-downloads
#
# Run (stdio):
#   podman run --rm -i \
#     -v ~/.local/share/mcp-uploads-downloads:/tmp/mcp-uploads:z \
#     -e WORDPRESS_URL=https://example.com \
#     -e WORDPRESS_USERNAME=admin \
#     -e WORDPRESS_APP_PASSWORD=xxxx_xxxx_xxxx_xxxx \
#     mcp-wordpress-crunchtools
#
# Run (HTTP):
#   podman run -d --name mcp-wordpress -p 127.0.0.1:8002:8000 \
#     -v ~/.local/share/mcp-uploads-downloads:/tmp/mcp-uploads:z \
#     --env-file ~/.config/mcp-env/mcp-wordpress-crunchtools.env \
#     mcp-wordpress-crunchtools \
#     --transport streamable-http --host 0.0.0.0

# Stage 1: Builder (has a shell, dnf and build tools)
FROM quay.io/hummingbird/python:latest-builder AS builder
USER 0
WORKDIR /app
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Stage 2: Runtime (distroless -- no shell, no package manager)
FROM quay.io/hummingbird/python:latest

# Labels for container metadata
LABEL name="mcp-wordpress-crunchtools" \
      version="0.5.0" \
      summary="Secure MCP server for WordPress content management" \
      description="A security-focused MCP server for WordPress built on Red Hat UBI" \
      maintainer="crunchtools.com" \
      url="https://github.com/crunchtools/mcp-wordpress" \
      io.k8s.display-name="MCP WordPress CrunchTools" \
      io.openshift.tags="mcp,wordpress,cms" \
      org.opencontainers.image.source="https://github.com/crunchtools/mcp-wordpress" \
      org.opencontainers.image.description="Secure MCP server for WordPress content management" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"

WORKDIR /app

COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"


# Verify the install. Exec form: this stage has no /bin/sh for RUN's shell form.
RUN ["python3", "-c", "from mcp_wordpress_crunchtools import main; print('Installation verified')"]

# Default: stdio transport (use -i with podman run)
# HTTP:    --transport streamable-http (use -d -p 8000:8000 with podman run)
EXPOSE 8000
ENTRYPOINT ["python", "-m", "mcp_wordpress_crunchtools"]
