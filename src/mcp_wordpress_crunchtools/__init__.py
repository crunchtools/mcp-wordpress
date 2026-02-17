"""MCP WordPress CrunchTools - Secure MCP server for WordPress.

A security-focused MCP server for WordPress content management:
posts, pages, media, and comments.

Usage:
    # Run directly
    mcp-wordpress-crunchtools

    # Or with Python module
    python -m mcp_wordpress_crunchtools

    # With uvx
    uvx mcp-wordpress-crunchtools

Environment Variables:
    WORDPRESS_URL: Required. WordPress site URL (e.g., https://example.com)
    WORDPRESS_USERNAME: Required. WordPress username
    WORDPRESS_APP_PASSWORD: Required. Application password (not user password)

Example with Claude Code:
    claude mcp add mcp-wordpress-crunchtools \\
        --env WORDPRESS_URL=https://example.com \\
        --env WORDPRESS_USERNAME=admin \\
        --env WORDPRESS_APP_PASSWORD=xxxx_xxxx_xxxx_xxxx \\
        -- uvx mcp-wordpress-crunchtools
"""

from .server import mcp

__version__ = "0.2.0"
__all__ = ["main", "mcp"]


def main() -> None:
    """Main entry point for the MCP server."""
    mcp.run()
