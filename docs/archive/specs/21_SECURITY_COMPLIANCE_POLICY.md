# Security, Compliance, and Policy

## Security Principle

CredenceAI ingests external data. That makes it useful and also makes it risky, because the internet is less a library and more a landfill with hyperlinks. Every external input must be treated as untrusted.

## Mandatory Protections

```text
robots.txt enforcement
domain-level rate limits
private IP blocking
SSRF protection
MIME validation
file-size limits
sandboxed browser execution
secret redaction in logs
takedown workflow
source-terms registry
audit logging
admin access control
```

## Crawl Security Gates

Stop processing if:

- URL resolves to private IP.
- URL redirects to private IP.
- File is executable.
- MIME type does not match signature.
- Domain repeatedly rate-limits.
- robots.txt disallows path.
- Payload exceeds size budget.
- Content appears malicious.
- Browser worker detects suspicious script behavior.

## SSRF Protection

The system must block:

- localhost.
- private IPv4 ranges.
- private IPv6 ranges.
- metadata service IPs.
- link-local addresses.
- internal DNS names.
- redirects to private/internal destinations.

## MIME and File Validation

Rules:

- Do not trust declared Content-Type alone.
- Validate file signature.
- Reject executable and high-risk file types.
- Quarantine suspicious payloads.
- Enforce file size limits before download where possible.

## Browser Worker Isolation

Browser workers must:

- Run sandboxed.
- Use strict CPU/memory/time budgets.
- Block downloads unless explicitly allowed.
- Disable unnecessary permissions.
- Avoid credentialed sessions unless explicitly configured.
- Emit security events for suspicious behavior.

## Source Terms Registry

Track per source/domain:

- Allowed use.
- Disallowed use.
- Crawling policy.
- Rate limits.
- Attribution requirements.
- Takedown process.
- Contact information.

## Audit Logging

Log:

- Job submission.
- Source calls.
- Raw payload reference.
- Quality decisions.
- Entity decisions.
- Crawl policy decisions.
- Agent decisions.
- Admin review decisions.
- Exports.
- Access control events.

## Access Control

Recommended roles:

| Role | Permissions |
|---|---|
| Viewer | Read trusted results and cards. |
| Analyst | Submit jobs and create collections. |
| Reviewer | Resolve review queue items. |
| Admin | Manage sources, budgets, users, policies. |
| Security Admin | Manage security settings and audit exports. |

## Data Privacy

- Redact secrets from logs.
- Avoid storing unnecessary personal data.
- Support deletion/takedown workflows.
- Tag sensitive fields.
- Apply retention policies.

## AI Governance

- AI outputs must be evidence-backed.
- AI decisions must be logged.
- AI cannot bypass deterministic policy gates.
- AI-generated summaries must include confidence and citations/provenance.
