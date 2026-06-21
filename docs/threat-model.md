# Threat model

## Assets

- Prompts
- Model outputs
- Tool calls
- Shell commands
- Repository metadata
- User/session attribution
- Cost and usage telemetry
- Detection findings

## Threats

- Secrets exposed to AI prompts or outputs
- AI agent reads sensitive local files
- AI agent executes dangerous shell commands
- Prompt injection causes unauthorized tool use
- MCP server abuse or unknown MCP server access
- AI-generated infrastructure introduces public exposure
- Telemetry backend becomes a sensitive data repository
- Findings expose masked but still sensitive context

## Controls

- Redact at collector layer
- Limit prompt/output capture
- Apply secret and DLP rules
- Alert on high-risk tool activity
- Store telemetry in a controlled backend
- Encrypt in transit and at rest
- Add authn/authz for APIs and dashboards
- Keep findings out of Git
