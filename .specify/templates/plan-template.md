# Implementation Plan: [Feature Name]

> **Spec ID:** XXX-feature-name
> **Status:** Planning | In Progress | Complete
> **Last Updated:** YYYY-MM-DD

## Summary

[1-2 sentence summary of implementation approach]

---

## Architecture

### Tool Flow

```
Claude Code / AI Client
    |
    v
server.py (@mcp.tool)
    | validates args
    v
tools/{category}.py (async function)
    | builds params/json
    v
client.py (httpx request)
    | Basic Auth header
    v
WordPress REST API
```

### Data Flow

1. [Step 1]
2. [Step 2]
3. [Step 3]

---

## Implementation Steps

### Phase 1: Tool Functions

- [ ] Add async functions to `tools/{category}.py`
- [ ] Add exports to `tools/__init__.py`
- [ ] Add `__all__` entries

### Phase 2: Server Registration

- [ ] Import tools in `server.py`
- [ ] Add `@mcp.tool()` wrappers with docstrings

### Phase 3: Tests

- [ ] Add mocked API tests in `test_tools.py`
- [ ] Update tool count assertion

### Phase 4: Quality Gates

- [ ] `uv run ruff check src tests`
- [ ] `uv run mypy src`
- [ ] `WORDPRESS_URL=https://wp.example.com WORDPRESS_USERNAME=test WORDPRESS_APP_PASSWORD=test uv run pytest -v`
- [ ] `gourmand --full .`
- [ ] `podman build -f Containerfile .`

---

## File Changes

### New Files

| File | Purpose |
|------|---------|
| `tools/new_group.py` | [Description] |

### Modified Files

| File | Changes |
|------|---------|
| `tools/__init__.py` | Add imports and `__all__` entries |
| `server.py` | Add `@mcp.tool()` wrappers |
| `tests/test_tools.py` | Add test class, update tool count |

---

## Testing Strategy

### Mocked Tests

- [ ] `test_*` — verify response shape with `_mock_wp_response()`
- [ ] Error case — verify error handling

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk 1] | [High/Med/Low] | [How to mitigate] |

---

## Changelog

| Date | Changes |
|------|---------|
| YYYY-MM-DD | Initial plan |
