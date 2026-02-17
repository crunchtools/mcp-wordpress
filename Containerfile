# MCP WordPress CrunchTools Container
#
# Build:
#   podman build -t mcp-wordpress-crunchtools -f Containerfile .
#
# Run:
#   podman run --rm -it \
#     -e WORDPRESS_URL=https://example.com \
#     -e WORDPRESS_USERNAME=admin \
#     -e WORDPRESS_APP_PASSWORD=xxxx_xxxx_xxxx_xxxx \
#     mcp-wordpress-crunchtools

FROM python:3.12-slim

LABEL maintainer="crunchtools.com"
LABEL description="Secure MCP server for WordPress content management"
LABEL version="0.2.0"

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

# Switch to non-root user
USER mcp

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the MCP server
ENTRYPOINT ["mcp-wordpress-crunchtools"]
