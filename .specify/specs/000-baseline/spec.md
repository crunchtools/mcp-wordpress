# Specification: Baseline

> **Spec ID:** 000-baseline
> **Status:** Implemented
> **Version:** 0.5.0
> **Author:** crunchtools.com
> **Date:** 2026-03-03

## Overview

Baseline specification for mcp-wordpress-crunchtools v0.5.0, documenting all 30 tools across 5 categories that provide secure access to the WordPress REST API.

---

## Tools (30)

### Site Tools (2)

| Tool | WordPress API Endpoint | Description |
|------|------------------------|-------------|
| `get_site_info` | `GET /settings` | Get site title, description, URL, timezone |
| `test_connection` | `GET /users/me` | Verify API credentials and connectivity |

### Post Tools (10)

| Tool | WordPress API Endpoint | Description |
|------|------------------------|-------------|
| `list_posts` | `GET /posts` | List posts with filtering and pagination |
| `get_post` | `GET /posts/{id}` | Get single post with full content |
| `search_posts` | `GET /posts?search=` | Search posts by keyword |
| `create_post` | `POST /posts` | Create a new post |
| `update_post` | `PATCH /posts/{id}` | Update an existing post |
| `delete_post` | `DELETE /posts/{id}` | Delete or trash a post |
| `list_revisions` | `GET /posts/{id}/revisions` | List post revisions |
| `get_revision` | `GET /posts/{id}/revisions/{rev_id}` | Get specific revision |
| `list_categories` | `GET /categories` | List available categories |
| `list_tags` | `GET /tags` | List available tags |

### Page Tools (6)

| Tool | WordPress API Endpoint | Description |
|------|------------------------|-------------|
| `list_pages` | `GET /pages` | List pages with filtering and pagination |
| `get_page` | `GET /pages/{id}` | Get single page with full content |
| `create_page` | `POST /pages` | Create a new page |
| `update_page` | `PATCH /pages/{id}` | Update an existing page |
| `delete_page` | `DELETE /pages/{id}` | Delete or trash a page |
| `list_page_revisions` | `GET /pages/{id}/revisions` | List page revisions |

### Media Tools (6)

| Tool | WordPress API Endpoint | Description |
|------|------------------------|-------------|
| `list_media` | `GET /media` | List media items with filtering |
| `get_media` | `GET /media/{id}` | Get single media item |
| `upload_media` | `POST /media` | Upload media file from local path |
| `update_media` | `PATCH /media/{id}` | Update media metadata |
| `delete_media` | `DELETE /media/{id}` | Delete media item |
| `get_media_url` | `GET /media/{id}` | Get public URL for media item |

### Comment Tools (6)

| Tool | WordPress API Endpoint | Description |
|------|------------------------|-------------|
| `list_comments` | `GET /comments` | List comments with filtering |
| `get_comment` | `GET /comments/{id}` | Get single comment |
| `create_comment` | `POST /comments` | Create a new comment |
| `update_comment` | `PATCH /comments/{id}` | Update an existing comment |
| `delete_comment` | `DELETE /comments/{id}` | Delete or trash a comment |
| `moderate_comment` | `PATCH /comments/{id}` | Moderate comment (approve/hold/spam/trash) |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WORDPRESS_URL` | Yes | — | WordPress site URL (e.g., https://example.com) |
| `WORDPRESS_USERNAME` | Yes | — | WordPress username |
| `WORDPRESS_APP_PASSWORD` | Yes | — | Application password (not user password) |
| `MCP_UPLOAD_DIR` | No | /tmp/mcp-uploads | Upload directory path for media |
| `MCP_WORDPRESS_PORT` | No | 8000 | HTTP port for streamable-http transport |

---

## Error Hierarchy

```
UserError
├── ConfigurationError
├── ValidationError
├── InvalidPostIdError
├── InvalidPageIdError
├── InvalidMediaIdError
├── InvalidCommentIdError
├── PostNotFoundError
├── PageNotFoundError
├── MediaNotFoundError
├── CommentNotFoundError
├── PermissionDeniedError
├── RateLimitError
└── WordPressApiError
```

---

## Module Structure

```
src/mcp_wordpress_crunchtools/
├── __init__.py          # Entry point, version, CLI args
├── __main__.py          # python -m support
├── server.py            # FastMCP server, @mcp.tool() wrappers (30 tools)
├── client.py            # httpx async client, WordPress REST API
├── config.py            # SecretStr credentials, API base URL
├── errors.py            # UserError hierarchy with credential scrubbing
├── models.py            # Pydantic models for input validation
└── tools/
    ├── __init__.py      # Re-exports all 30 tool functions
    ├── site.py          # get_site_info, test_connection
    ├── posts.py         # 10 post/revision/category/tag tools
    ├── pages.py         # 6 page tools
    ├── media.py         # 6 media tools
    └── comments.py      # 6 comment tools
```

---

## Test Coverage

| Test File | Tests | What It Covers |
|-----------|------:|----------------|
| `test_tools.py` | 30+ | Tool count, imports, mocked API (site, posts, pages, media, comments), error handling |
| `test_validation.py` | 25+ | Pydantic models, ID validation, status/format enums |
| `test_media.py` | 5 | File upload validation (paths, MIME types, size limits) |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 0.5.0 | 2026-03-03 | V2 architecture: governance, mocked tests, version sync |
| 0.4.1 | 2026-03-01 | MCP Registry publication, server.json |
| 0.4.0 | 2026-02-24 | Media upload from local files |
| 0.3.0 | 2026-02-19 | Initial release with 30 tools |
