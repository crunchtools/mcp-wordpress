# Security Policy

## Security Features

This MCP server implements multiple security measures to protect WordPress credentials and prevent attacks:

### Credential Protection

1. **SecretStr Storage**: All credentials (passwords) are stored as Pydantic `SecretStr` types
2. **No Logging**: Credentials are never written to logs or debug output
3. **Safe Repr**: `__repr__` and `__str__` methods never expose sensitive data
4. **Error Sanitization**: Error messages automatically replace any credential values with `***`

### SSRF Prevention

1. **Hardcoded API Path**: The REST API path (`/wp-json/wp/v2/`) is hardcoded and cannot be overridden
2. **URL Validation**: WordPress URL is validated and normalized on startup
3. **No URL Parameters**: Users cannot specify arbitrary URLs in tool calls

### Input Validation

1. **Pydantic Models**: All tool inputs are validated through Pydantic models
2. **Type Enforcement**: Strict type checking prevents injection attacks
3. **Length Limits**: String fields have maximum length limits
4. **Enum Validation**: Status fields restricted to valid values only

### Network Security

1. **TLS Enforced**: All requests use HTTPS with certificate validation
2. **Timeout**: 30-second timeout on all requests
3. **Size Limits**: 10MB response size limit prevents memory exhaustion

### Authentication

1. **Application Passwords**: Uses WordPress Application Passwords (not user passwords)
2. **Basic Auth**: Credentials sent via Authorization header, not URL
3. **No Token Storage**: Tokens are not persisted to disk

## Reporting a Vulnerability

If you discover a security vulnerability, please report it via email to the repository maintainers. Do not open a public issue.

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and work to release a fix promptly.

## Scope

### In Scope
- Credential exposure
- SSRF vulnerabilities
- Injection attacks
- Authentication bypass
- Information disclosure

### Out of Scope
- WordPress core vulnerabilities
- Vulnerabilities in dependencies (report to upstream)
- Social engineering attacks
- Physical access attacks

## Best Practices for Users

1. **Use Application Passwords**: Never use your main WordPress password
2. **Limit Permissions**: Create a WordPress user with only necessary capabilities
3. **HTTPS Only**: Always use HTTPS for your WordPress site
4. **Environment Variables**: Store credentials in environment variables, not config files
5. **Rotate Passwords**: Periodically generate new application passwords
6. **Monitor Access**: Review WordPress login logs regularly
