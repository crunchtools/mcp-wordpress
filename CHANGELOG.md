# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

Entries prior to 2026-09-19 are back-filled from GitHub Release notes (RT #1484).

## [Unreleased]

### Security

- Upgraded locked dependencies within their declared ranges to clear the
  advisories the fleet dependency audit found (anyio, authlib, certifi, cryptography, dnspython, fastmcp, joserfc, opentelemetry-api, pydantic-settings, pygments, pyjwt, python-dotenv, requests, urllib3).

## [0.8.0] - 2026-10-27

### Added
- `wordpress_edit_post`, `wordpress_edit_page` and `wordpress_edit_draft`: replace text in
  the saved source on the server, so an edit never resends the whole post. `edit_draft`
  refuses any post that is not a draft or pending, and its write keeps that status.
- `expected_version` on the post and page update and edit tools: when given, the write is
  refused if the item changed since it was read. `get_post` and `get_page` return the
  `version` to pass: a hash of `modified_gmt` and the raw title, content and excerpt, so
  two writes inside the same second are still told apart.

### Changed
- `get_post`, `get_page` and `get_revision` return the saved source (`context=edit`):
  block markup kept, no plugin output such as the ez-toc table of contents. They used to
  return the rendered page, which corrupted a post when written back.
- `update_post` and `update_page` refuse content that is rendered output or that strips
  the item's block markup, and return a summary (id, title, status, version, link)
  instead of the content.

## [0.7.0] - 2026-10-20

### Changed

- Container base images pinned to `quay.io/hummingbird/python:3.14*` instead of
  `latest`, which moved to Python 3.15.0 on 2026-10-20 (crunchtools/constitution#66).

## [0.6.1] - 2026-10-17

### Fixed
- Every integer ID argument (`post_id`, `page_id`, `media_id`, `comment_id`,
  `revision_id`, and the `post` argument of `list_comments` and `create_comment`)
  now publishes `minimum: 1` in the tool schema, so `0` and negative IDs are rejected.
- The tests import `test_connection` under an alias so pytest no longer collects it
  and makes a real request to example.com.

## [0.6.0] - 2026-10-10

### Added
- The 17 tools that only read (the `get_*`, `list_*` and `search_posts` tools,
  `get_site_info`, `test_connection`) publish `readOnlyHint: true`. A gateway
  uses it to decide whether an invalid optional argument may be dropped or must
  refuse the call (crunchtools/constitution#35).
- Tests pin every registered tool into `READ_ONLY` or `WRITES`, and check that
  each read-only tool sends WordPress nothing but GET.

### Fixed
- The Containerfile `version` label said 0.5.0 through the 0.5.1 release; it
  carries the release version again.

### Changed
- Inherits constitution v1.22.0; the workflow pins and the pre-commit hook rev
  move with it.
- Constitution is now a v1.18.0 manifest: only repo-specific facts remain;
  fleet and profile rules apply by reference.
- Constitution validation is pinned via `.github/workflows/constitution.yml`.
- Dependabot auto-merges GitHub Actions minor and patch updates.

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
