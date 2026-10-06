# mcp-wordpress-crunchtools Constitution

> **Version:** 1.1.0
> **Ratified:** 2026-03-03
> **Amended:** 2026-10-02
> **Status:** Active
> **Inherits:** [crunchtools/constitution](https://github.com/crunchtools/constitution) v1.20.0
> **Profile:** MCP Server

This file holds what is specific to mcp-wordpress. The fleet rules and the
MCP Server profile (five-layer security model, two-layer tools, distribution
channels, transport modes, quality gates, Gourmand) apply at the inherited
version and are checked against this repo's files by `constitution.yml`. They
are not restated here.

## Security Model Specifics

- **Credentials:** `WORDPRESS_URL`, `WORDPRESS_USERNAME` and
  `WORDPRESS_APP_PASSWORD` (a WordPress application password). The password
  is `SecretStr`, environment-only, never shown by `Config`
  `repr()`/`str()`, and scrubbed from error messages by `WordPressApiError`.
- **Input limits:** post, page, media and comment IDs are integers; every
  create/update input is a Pydantic model; status and format are enums.
- **API:** auth travels in a Basic Auth header. The REST path
  `/wp-json/wp/v2` is hardcoded, which prevents SSRF. TLS is always
  validated; requests time out after 30s; responses above 10 MB are
  rejected.
- **Media upload:** the one local filesystem read. Upload paths MUST be
  absolute, the file must exist (errors carry container mount hints), the
  MIME type is detected, and files above 50 MB are refused. `test_media.py`
  covers each.

## Single-Instance Design

The server talks to one WordPress site, set by `WORDPRESS_URL`. The URL is
validated at startup and held immutably in the `Config` singleton.

## Instance

| Context | Name |
|---------|------|
| GitHub repo | `crunchtools/mcp-wordpress` |
| PyPI package | `mcp-wordpress-crunchtools` |
| Python module | `mcp_wordpress_crunchtools` |
| Container image | `quay.io/crunchtools/mcp-wordpress` |
| systemd service | `mcp-wordpress.service` |
| HTTP port | 8000 |

## History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-03 | Initial constitution |
| 1.0.1 | 2026-03-16 | Container Conventions section added |
| 1.1.0 | 2026-10-02 | Manifest under constitution v1.18.0: profile restatement removed, mcp-wordpress specifics kept |
