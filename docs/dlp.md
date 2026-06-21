# DLP and secret handling

AgentLens includes starter regex rules for common secrets and sensitive data. Treat these as a baseline, not a complete DLP program.

## Included examples

- AWS access keys
- GitHub tokens
- Slack tokens
- AI provider keys
- Private keys
- JWTs
- SSNs
- Credit card-like values
- Database URLs
- Email addresses

## Recommended additions

- Gitleaks
- TruffleHog
- detect-secrets
- Microsoft Presidio
- Organization-specific regexes
- Customer/project codenames
- Internal hostnames and domains

## Important

Prompt and output logging can capture sensitive information. Decide early whether prompts/outputs should be stored, redacted, sampled, or dropped.
