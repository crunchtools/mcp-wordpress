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

FROM python:3.12-slim

LABEL maintainer="crunchtools.com"
LABEL description="Secure MCP server for WordPress content management"
LABEL version="0.3.0"

# Create non-root user
RUN useradd --create-home --shell /bin/bash mcp

# Set working directory
WORKDIR /app

# Install uv for fast package management
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN uv pip install --system --no-cache .

# Create upload directory so server works with or without host volume mount
RUN mkdir -p /tmp/mcp-uploads && chown mcp:mcp /tmp/mcp-uploads

# Switch to non-root user
USER mcp

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port for HTTP transports
EXPOSE 8000

# Run the MCP server
ENTRYPOINT ["mcp-wordpress-crunchtools"]
