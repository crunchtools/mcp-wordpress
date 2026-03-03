# mcp-wordpress-crunchtools Constitution

> **Version:** 1.0.0
> **Ratified:** 2026-03-03
> **Status:** Active
> **Inherits:** [crunchtools/constitution](https://github.com/crunchtools/constitution) v1.0.0
> **Profile:** MCP Server

This constitution establishes the core principles, constraints, and workflows that govern all development on mcp-wordpress-crunchtools.

---

## I. Core Principles

### 1. Five-Layer Security Model

Every change MUST preserve all five security layers. No exceptions.

**Layer 1 — Credential Protection:**
- WORDPRESS_APP_PASSWORD stored as `SecretStr` (never logged or exposed)
- Environment-variable-only storage
- Automatic scrubbing from error messages via `WordPressApiError`

**Layer 2 — Input Validation:**
- Integer validation for post/page/media/comment IDs
- Pydantic models for all create/update inputs
- Status and format enum enforcement

**Layer 3 — API Hardening:**
- Auth via Basic Auth header (base64-encoded credentials)
- Hardcoded REST API path `/wp-json/wp/v2` (prevents SSRF)
- Mandatory TLS certificate validation (httpx default)
- Request timeout enforcement (30s)
- Response size limits (10MB)

**Layer 4 — Output Sanitization:**
- `WordPressApiError` redacts credential values from any error messages
- Safe `__repr__()` and `__str__()` on Config that never expose passwords
- Structured errors without internal details

**Layer 5 — Supply Chain Security:**
- Weekly automated CVE scanning via GitHub Actions
- Hummingbird container base images (minimal CVE surface)
- Gourmand AI slop detection gating all PRs

### 2. Two-Layer Tool Architecture

Tools follow a strict two-layer pattern:
- `server.py` — `@mcp.tool()` decorated functions that validate args and delegate
- `tools/*.py` — Pure async functions that call `client.py` HTTP methods

Never put business logic in `server.py`. Never put MCP registration in `tools/*.py`.

### 3. Single-Instance Design

The server connects to a single WordPress instance configured via WORDPRESS_URL. The URL is validated at startup and stored immutably in the Config singleton.

### 4. Three Distribution Channels

Every release MUST be available through all three channels simultaneously:

| Channel | Command | Use Case |
|---------|---------|----------|
| uvx | `uvx mcp-wordpress-crunchtools` | Zero-install, Claude Code |
| pip | `pip install mcp-wordpress-crunchtools` | Virtual environments |
| Container | `podman run quay.io/crunchtools/mcp-wordpress` | Isolated, systemd |

### 5. Three Transport Modes

The server MUST support all three MCP transports:
- **stdio** (default) — spawned per-session by Claude Code
- **SSE** — legacy HTTP transport
- **streamable-http** — production HTTP, systemd-managed containers

### 6. Semantic Versioning

Follow [Semantic Versioning 2.0.0](https://semver.org/) strictly.

**MAJOR** (breaking changes — consumers must update):
- Removed or renamed tools
- Changed tool parameter names or types
- Renamed environment variables
- Changed default behavior of existing tools

**MINOR** (new functionality — backwards compatible):
- New tools added
- New optional parameters on existing tools
- New tool groups

**PATCH** (fixes — no functional change):
- Bug fixes in existing tools
- Test additions or improvements
- Security patches (dependency updates)

**No version bump required** (infrastructure, not shipped):
- CI/CD changes (workflows, gourmand config)
- Documentation (README, CLAUDE.md, SECURITY.md)
- Issue templates, pre-commit config
- Governance files (.specify/)

**Version bump happens at release time, not per-commit.** Multiple commits can accumulate between releases. The version in `pyproject.toml`, `server.py`, and `__init__.py` is bumped when cutting a release tag.

### 7. AI Code Quality

All code MUST pass Gourmand checks before merge. Zero violations required.

---

## II. Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.10+ |
| MCP Framework | FastMCP | Latest |
| HTTP Client | httpx | Latest |
| Validation | Pydantic | v2 |
| Container Base | Hummingbird | Latest |
| Package Manager | uv | Latest |
| Build System | hatchling | Latest |
| Linter | ruff | Latest |
| Type Checker | mypy (strict) | Latest |
| Tests | pytest + pytest-asyncio | Latest |
| Slop Detector | gourmand | Latest |

---

## III. Testing Standards

### Mocked API Tests (MANDATORY)

Every tool MUST have a corresponding mocked test. Tests use `httpx.AsyncClient` mocking — no live API calls, no credentials required in CI.

**Pattern:**
1. Build a mock `httpx.Response` with `_mock_wp_response()` helper
2. Patch `httpx.AsyncClient.request` via `_patch_wp_client()` context manager
3. Call the tool function directly (not the `wordpress_` wrapper)
4. Assert response structure and values

**Note:** WordPress REST API returns JSON responses, so mocks return JSON content.

**Singleton reset:** The `_reset_client_singleton` autouse fixture resets `_client` in client.py and `_config` in config.py between every test to prevent state leakage.

**Tool count assertion:** `test_tool_count` MUST be updated whenever tools are added or removed. This catches accidental regressions.

### Input Validation Tests

Pydantic model validation tests in `test_validation.py`:
- PostInput, PageInput, MediaInput, CommentInput models
- ID validation functions (validate_post_id, etc.)
- Status and format enum enforcement

### Media Upload Tests

File validation tests in `test_media.py`:
- Path validation (absolute paths only)
- File existence checks with container mount hints
- MIME type detection
- Size limit enforcement

### Error Hierarchy Tests

Error handling tests in `test_tools.py`:
- Error class hierarchy (all inherit from UserError)
- Error message formatting
- Password sanitization in WordPressApiError

---

## IV. Gourmand (AI Slop Detection)

All code MUST pass `gourmand --full .` with **zero violations** before merge. Gourmand is a CI gate in GitHub Actions.

### Configuration

- `gourmand.toml` — Check settings, excluded paths
- `gourmand-exceptions.toml` — Documented exceptions with justifications
- `.gourmand-cache/` — Must be in `.gitignore`

### Exception Policy

Exceptions MUST have documented justifications in `gourmand-exceptions.toml`. Acceptable reasons:
- Standard API patterns (HTTP status codes)
- Test-specific patterns (intentional invalid input)
- Framework requirements (CLAUDE.md for Claude Code)

---

## V. Code Quality Gates

Every code change must pass through these gates in order:

1. **Lint** — `uv run ruff check src tests`
2. **Type Check** — `uv run mypy src`
3. **Tests** — `WORDPRESS_URL=https://wp.example.com WORDPRESS_USERNAME=test WORDPRESS_APP_PASSWORD=test uv run pytest -v`
4. **Gourmand** — `gourmand --full .` (zero violations)
5. **Container Build** — `podman build -f Containerfile .`

### CI Pipeline (GitHub Actions)

| Job | What it does | Gates PRs |
|-----|-------------|-----------|
| test | Lint + mypy + pytest (Python 3.10-3.12) | Yes |
| gourmand | AI slop detection | Yes |
| build-container | Containerfile builds | Yes |
| security | Weekly CVE scan | Scheduled |
| publish | PyPI trusted publishing | On release tag |
| container | Quay.io + GHCR push | On release tag |

---

## VI. Naming Conventions

| Context | Name |
|---------|------|
| GitHub repo | `crunchtools/mcp-wordpress` |
| PyPI package | `mcp-wordpress-crunchtools` |
| CLI command | `mcp-wordpress-crunchtools` |
| Python module | `mcp_wordpress_crunchtools` |
| Container image | `quay.io/crunchtools/mcp-wordpress` |
| systemd service | `mcp-wordpress.service` |
| HTTP port | 8000 |
| License | AGPL-3.0-or-later |

---

## VII. Development Workflow

### Adding a New Tool

1. Add the async function to `tools/{category}.py`
2. Export it from `tools/__init__.py`
3. Import it in `server.py` and register with `@mcp.tool()`
4. Add a mocked test in `tests/test_tools.py`
5. Update the tool count in `test_tool_count`
6. Run all five quality gates
7. Update CLAUDE.md tool listing

### Adding a New Tool Group

1. Create `tools/new_group.py` with async functions
2. Add imports and `__all__` entries in `tools/__init__.py`
3. Add `@mcp.tool()` wrappers in `server.py`
4. Add a `TestNewGroupTools` class in `tests/test_tools.py`
5. Run all five quality gates

---

## VIII. Governance

### Amendment Process

1. Create a PR with proposed changes to this constitution
2. Document rationale in PR description
3. Require maintainer approval
4. Update version number upon merge

### Ratification History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-03 | Initial constitution |
