# MCP WordPress CrunchTools Container
#
# Build:
#   podman build -t mcp-wordpress-crunchtools -f Containerfile .
#
# Setup (create upload directory on host before first run):
#   mkdir -p ~/.local/share/mcp-wordpress/uploads
#
# Run:
#   podman run --rm -it \
#     -v ~/.local/share/mcp-wordpress/uploads:/tmp/mcp-uploads:Z \
#     -e WORDPRESS_URL=https://example.com \
#     -e WORDPRESS_USERNAME=admin \
#     -e WORDPRESS_APP_PASSWORD=xxxx_xxxx_xxxx_xxxx \
#     mcp-wordpress-crunchtools

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

# Run the MCP server
ENTRYPOINT ["mcp-wordpress-crunchtools"]
