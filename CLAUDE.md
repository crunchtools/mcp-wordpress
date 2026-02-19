# MCP WordPress CrunchTools

Secure MCP server for WordPress content management.

## Quick Start

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run linting
uv run ruff check src tests

# Run type checking
uv run mypy src
```

## Environment Variables

Required environment variables:

- `WORDPRESS_URL`: WordPress site URL (e.g., `https://example.com`)
- `WORDPRESS_USERNAME`: WordPress username
- `WORDPRESS_APP_PASSWORD`: Application password (generate at Users -> Profile -> Application Passwords)

## Architecture

```
src/mcp_wordpress_crunchtools/
├── __init__.py          # Entry point, main()
├── __main__.py          # python -m support
├── server.py            # FastMCP server with @mcp.tool() decorators
├── config.py            # SecretStr config for WP credentials
├── client.py            # Async httpx client for WP REST API
├── errors.py            # UserError hierarchy
├── models.py            # Pydantic validation models
└── tools/
    ├── __init__.py      # Export all tools
    ├── posts.py         # Post CRUD operations
    ├── pages.py         # Page CRUD operations
    ├── media.py         # Media upload/management
    ├── comments.py      # Comment management
    └── site.py          # Site info/status
```

## Tools (30 total)

### Site Tools (2)
- `wordpress_get_site_info` - Get site title, description, URL, timezone
- `wordpress_test_connection` - Verify API credentials work

### Post Tools (10)
- `wordpress_list_posts` - List with filtering/pagination
- `wordpress_get_post` - Get single post by ID
- `wordpress_search_posts` - Search by keyword
- `wordpress_create_post` - Create new post
- `wordpress_update_post` - Update existing post
- `wordpress_delete_post` - Delete/trash post
- `wordpress_list_revisions` - List post revisions
- `wordpress_get_revision` - Get specific revision
- `wordpress_list_categories` - List categories
- `wordpress_list_tags` - List tags

### Page Tools (6)
- `wordpress_list_pages` - List with filtering
- `wordpress_get_page` - Get single page
- `wordpress_create_page` - Create new page
- `wordpress_update_page` - Update existing page
- `wordpress_delete_page` - Delete/trash page
- `wordpress_list_page_revisions` - List page revisions

### Media Tools (6)
- `wordpress_list_media` - List media items
- `wordpress_get_media` - Get media details
- `wordpress_upload_media` - Upload from local file path
- `wordpress_update_media` - Update metadata
- `wordpress_delete_media` - Delete media
- `wordpress_get_media_url` - Get public URL

### Comment Tools (6)
- `wordpress_list_comments` - List with filtering
- `wordpress_get_comment` - Get single comment
- `wordpress_create_comment` - Add comment to post
- `wordpress_update_comment` - Update comment
- `wordpress_delete_comment` - Delete comment
- `wordpress_moderate_comment` - Approve/hold/spam/trash

## Security Features

- Credentials stored as `SecretStr` to prevent logging
- Hardcoded REST API path (`/wp-json/wp/v2/`) to prevent SSRF
- Input validation via Pydantic models
- Response size limits (10MB)
- Request timeouts (30s)
- Sanitized error messages (no credential leaks)
- TLS certificate validation enforced

## Usage with Claude Code

```bash
claude mcp add mcp-wordpress-crunchtools \
    --env WORDPRESS_URL=https://example.com \
    --env WORDPRESS_USERNAME=admin \
    --env WORDPRESS_APP_PASSWORD=xxxx_xxxx_xxxx_xxxx \
    -- uvx mcp-wordpress-crunchtools
```

## Development

```bash
# Format code
uv run ruff format src tests

# Fix linting issues
uv run ruff check --fix src tests
```
