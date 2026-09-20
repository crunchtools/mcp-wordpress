# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

Entries prior to 2026-09-19 are back-filled from GitHub Release notes (RT #1484).

## [Unreleased]

## [0.5.1] - 2026-09-20

### Fixed
- The v0.5.0 tag's `Container Build & Push` run pushed to Quay.io but failed
  before reaching GHCR; re-running that historical workflow now fails outright
  because it pins `aquasecurity/trivy-action@0.34.1`, a version that no longer
  resolves upstream (fixed on main by #7's Trivy re-pin, well after v0.5.0
  shipped). Cutting v0.5.1 from current main — which has the Trivy fix, the
  split quay/ghcr jobs, and every dependency bump since — so the release
  actually lands in both registries.

## [0.5.0] - 2026-03-03

Upgrade to V2 architecture — the last of 8 CrunchTools MCP servers to reach V2
standard. No breaking changes: same 30 tools, same `wordpress_` prefix, same env
vars.

### Added
- AGPL-3.0 LICENSE.
- `.specify/` project governance (constitution, baseline spec, templates).
- Gourmand AI slop detection config.
- Pre-commit hooks (ruff check + format).
- GitHub issue templates (bug report, feature request).
- 85 tests (up from ~40): full mocked API tests for all 30 tools across 5
  categories, with shared fixtures in `conftest.py`.

### Changed
- All 4 version locations synced to 0.5.0.

## [0.3.0] - 2026-02-19

No GitHub Release was created for this tag, so no authored release notes exist to
back-fill from.

## [0.2.1] - 2026-02-16

Improved media upload experience for container deployments. Fixes #2.

### Changed
- **Updated tool description**: `wordpress_upload_media` includes a CONTAINER
  NOTE about the filesystem boundary.
- **Server instructions updated**: mount path info is now surfaced to MCP clients
  on connection.
- **New tests**: added `test_media.py` covering file upload validation.

### Fixed
- **Better error messages**: file-not-found errors now explain the container
  mount path requirement (`/tmp/mcp-uploads/`).

## [0.2.0] - 2026-02-16

### Changed
- **Breaking:** `wordpress_upload_media` now takes `file_path` (absolute path on
  disk) instead of `file_data` (base64 string) and `filename`. The MCP server
  container must have the upload directory mounted (e.g.
  `-v /tmp/mcp-uploads:/tmp/mcp-uploads:Z`).

### Fixed
- **Media uploads locking up Claude Code** — `upload_media` accepts a file path
  instead of base64-encoded data, eliminating multi-MB payloads over MCP stdio
  (#1).
- **Multipart upload Content-Type** — removed the default
  `Content-Type: application/json` header from the HTTP client, which was leaking
  into file uploads and causing WordPress to reject them.

## [0.1.0] - 2026-02-15

Initial release. Secure MCP server for WordPress content management.

### Added
- **30 tools** for posts, pages, media, and comments.
- **Security-focused**: credentials protected, input validation, SSRF prevention.
- **Developer workflow**: scheduled publishing, revisions, search.
