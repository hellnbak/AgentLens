# Changelog

## Unreleased

- Fixed detector startup crash caused by numeric YAML alias keys in pricing files.
- Hardened pricing alias loading by coercing alias keys to strings.

## 0.1.0 - Initial public starter

- Claude Code OpenTelemetry local collector stack.
- Detector/enricher service with YAML rule packs.
- Cost, DLP, secret, shell, Git, IaC, MCP, prompt-injection, endpoint tamper, and IdP risk scaffolding.
- Endpoint collector agent with watchdog and tamper-evident controls.
- EDR scaffolding for CrowdStrike, SentinelOne, and Microsoft Defender.
- Optional IdP enrichment for Okta and JumpCloud plus static mapping fallback.
- AWS and GCP deployment scaffolding.
- FSL-1.1-Apache-2.0 future license.

## Unreleased

- Hardened macOS/Linux endpoint installer UX with dry-run, no-start, preflight, and environment overrides.
- Added release checksum and signing helpers plus GitHub release workflow.
- Added optional ClickHouse backend config and init SQL.
- Added Splunk HEC, Elastic/OpenSearch, and S3 exporter examples.
- Added spend, endpoint-health, and security-findings Grafana dashboards.
- Added Cursor/local-agent adapter docs, MCP inventory scaffold, repo enrichment docs, and EDR integration scaffolds for CrowdStrike, SentinelOne, and Microsoft Defender.
