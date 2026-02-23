# MCP WordPress CrunchTools

A secure MCP (Model Context Protocol) server for WordPress content management. Designed for developers publishing about their work.

## Overview

This MCP server is designed to be:

- **Secure by default** - Comprehensive input validation, credential protection, and SSRF prevention
- **No third-party services** - Runs locally via stdio, your credentials never leave your machine
- **Cross-platform** - Works on Linux, macOS, and Windows
- **Automatically updated** - GitHub Actions monitor for CVEs and update dependencies
- **Containerized** - Available at `quay.io/crunchtools/mcp-wordpress`

## Naming Convention

| Component | Name |
|-----------|------|
| GitHub repo | [crunchtools/mcp-wordpress](https://github.com/crunchtools/mcp-wordpress) |
| Container | `quay.io/crunchtools/mcp-wordpress` |
| Python package (PyPI) | `mcp-wordpress-crunchtools` |
| CLI command | `mcp-wordpress-crunchtools` |
| Module import | `mcp_wordpress_crunchtools` |

## Features

- **30 Tools** for posts, pages, media, and comments
- **Security-focused**: Credentials protected, input validation, SSRF prevention
- **Developer workflow**: Scheduled publishing, revisions, search
- **Easy integration**: Works with Claude Code and other MCP clients

## Installation

### With uvx (recommended)

```bash
uvx mcp-wordpress-crunchtools
```

### With pip

```bash
pip install mcp-wordpress-crunchtools
mcp-wordpress-crunchtools
```

### With Container

```bash
# Create a shared upload directory (required before first run)
mkdir -p ~/.local/share/mcp-uploads-downloads

podman run -v ~/.local/share/mcp-uploads-downloads:/tmp/mcp-uploads:z \
  -e WORDPRESS_URL=https://example.com \
  -e WORDPRESS_USERNAME=admin \
  -e WORDPRESS_APP_PASSWORD='xxxx xxxx xxxx xxxx' \
  quay.io/crunchtools/mcp-wordpress
```

> **SELinux note:** Use `:z` (lowercase, shared) instead of `:Z` (uppercase, private).
> MCP servers run as long-lived stdio processes. With `:Z`, files copied into the
> directory after container start won't have the container's private MCS label and
> will be invisible inside the container. The `:z` flag sets a shared
> `container_file_t` context that all containers and the host can read/write.
>
> **Tip:** Use the same shared directory (`~/.local/share/mcp-uploads-downloads/`)
> across multiple MCP container servers (e.g., mcp-wordpress and mcp-gemini) so
> generated files are immediately available for upload without copying.

### From source

```bash
git clone https://github.com/crunchtools/mcp-wordpress.git
cd mcp-wordpress
uv sync --all-extras
uv run mcp-wordpress-crunchtools
```

## Configuration

Set these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `WORDPRESS_URL` | WordPress site URL | `https://example.com` |
| `WORDPRESS_USERNAME` | WordPress username | `admin` |
| `WORDPRESS_APP_PASSWORD` | Application password | `xxxx xxxx xxxx xxxx` |
| `MCP_UPLOAD_DIR` | Upload directory inside container (optional) | `/tmp/mcp-uploads` (default) |

### Creating an Application Password

1. Log in to WordPress admin
2. Go to **Users → Profile**
3. Scroll to **Application Passwords**
4. Enter a name (e.g., "MCP Server") and click **Add New**
5. Copy the generated password (shown once)

## Usage with Claude Code

### Using uvx (recommended)

```bash
claude mcp add mcp-wordpress-crunchtools \
    --env WORDPRESS_URL=https://example.com \
    --env WORDPRESS_USERNAME=admin \
    --env WORDPRESS_APP_PASSWORD="xxxx xxxx xxxx xxxx" \
    -- uvx mcp-wordpress-crunchtools
```

### Using pip

```bash
pip install mcp-wordpress-crunchtools

claude mcp add mcp-wordpress-crunchtools \
    --env WORDPRESS_URL=https://example.com \
    --env WORDPRESS_USERNAME=admin \
    --env WORDPRESS_APP_PASSWORD="xxxx xxxx xxxx xxxx" \
    -- mcp-wordpress-crunchtools
```

### Using Container

```bash
# Create a shared upload directory (required before first run)
mkdir -p ~/.local/share/mcp-uploads-downloads

claude mcp add mcp-wordpress-crunchtools \
    --env WORDPRESS_URL=https://example.com \
    --env WORDPRESS_USERNAME=admin \
    --env WORDPRESS_APP_PASSWORD="xxxx xxxx xxxx xxxx" \
    -- podman run -i --rm \
        -v ~/.local/share/mcp-uploads-downloads:/tmp/mcp-uploads:z \
        -e WORDPRESS_URL \
        -e WORDPRESS_USERNAME \
        -e WORDPRESS_APP_PASSWORD \
        quay.io/crunchtools/mcp-wordpress
```

## Available Tools

### Site Tools
| Tool | Description |
|------|-------------|
| `wordpress_get_site_info` | Get site title, description, URL, timezone |
| `wordpress_test_connection` | Verify API credentials work |

### Post Tools
| Tool | Description |
|------|-------------|
| `wordpress_list_posts` | List posts with filtering (status, category, search) |
| `wordpress_get_post` | Get single post by ID with full content |
| `wordpress_search_posts` | Search posts by keyword |
| `wordpress_create_post` | Create new post (supports scheduling) |
| `wordpress_update_post` | Update existing post |
| `wordpress_delete_post` | Delete/trash a post |
| `wordpress_list_revisions` | List revisions for a post |
| `wordpress_get_revision` | Get specific revision content |
| `wordpress_list_categories` | List available categories |
| `wordpress_list_tags` | List available tags |

### Page Tools
| Tool | Description |
|------|-------------|
| `wordpress_list_pages` | List pages with filtering |
| `wordpress_get_page` | Get single page by ID |
| `wordpress_create_page` | Create new page |
| `wordpress_update_page` | Update existing page |
| `wordpress_delete_page` | Delete/trash a page |
| `wordpress_list_page_revisions` | List page revisions |

### Media Tools
| Tool | Description |
|------|-------------|
| `wordpress_list_media` | List media items |
| `wordpress_get_media` | Get media item details |
| `wordpress_upload_media` | Upload file from local path |
| `wordpress_update_media` | Update media metadata |
| `wordpress_delete_media` | Delete media item |
| `wordpress_get_media_url` | Get public URL for media |

### Comment Tools
| Tool | Description |
|------|-------------|
| `wordpress_list_comments` | List comments with filtering |
| `wordpress_get_comment` | Get single comment |
| `wordpress_create_comment` | Add a comment to a post |
| `wordpress_update_comment` | Update comment content/status |
| `wordpress_delete_comment` | Delete a comment |
| `wordpress_moderate_comment` | Approve, hold, spam, or trash |

## Examples

### Create a Draft Post

```
Create a new WordPress post titled "My Technical Article" with the content below. Keep it as a draft.
```

### Schedule a Post

```
Update post ID 123 to publish on December 25, 2024 at 10:00 AM.
```

### Upload an Image

```
Upload this image to WordPress and set the alt text to "Architecture diagram".
```

### Find and Moderate Comments

```
List all comments in "hold" status and approve the legitimate ones.
```

## Security

- **Credential Protection**: All credentials stored as `SecretStr`, never logged
- **SSRF Prevention**: REST API path hardcoded, cannot be overridden
- **Input Validation**: All inputs validated via Pydantic models
- **Rate Limiting**: Handles WordPress rate limits gracefully
- **TLS Enforcement**: All requests use HTTPS with certificate validation
- **Size Limits**: Response size limited to 10MB to prevent memory issues
- **Timeout**: All requests timeout after 30 seconds

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run linting
uv run ruff check src tests

# Run type checking
uv run mypy src

# Format code
uv run ruff format src tests
```

## License

AGPL-3.0-or-later

## Credits

Built by [crunchtools.com](https://crunchtools.com)
