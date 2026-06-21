# AgentLens

Open-source OpenTelemetry-based observability, spend monitoring, security analytics, and DLP detection for Claude Code and other AI development agents.

AgentLens gives security and engineering teams a local-first way to collect AI coding assistant telemetry, normalize it, detect risky activity, and export useful findings to your observability/SIEM stack.

## Why this exists

AI coding agents are quickly becoming part of normal software delivery, but most organizations still lack practical answers to basic governance questions:

- Who is using AI coding agents?
- Which repos and teams drive the most spend?
- Which models are being used?
- Are prompts, outputs, or tool calls exposing secrets or sensitive data?
- Are agents running dangerous shell commands?
- Are MCP servers, hooks, or tools being used in risky ways?
- Can security teams audit a session after an incident?

Claude Code is the first supported target because it can export OpenTelemetry metrics, log events, and optional traces through OTLP. This project is designed so additional AI development platforms can be added as adapters over time.

## What you get in v0.1

- Docker Compose local stack
- OpenTelemetry Collector config for OTLP gRPC and HTTP
- Claude Code setup helper
- Telemetry file export for logs and traces
- Prometheus metrics endpoint
- Python detector/enricher service
- YAML rules for secrets, DLP, shell risk, git risk, IaC risk, and MCP risk
- Cost/pricing configuration files
- JSONL findings output
- Security/risk API
- Level 1 action router for audit/webhook/Slack/Jira response actions
- Level 2 CI/PR policy gate for GitHub/GitLab-style merge blocking
- Prometheus metrics for findings, actions, and estimated spend
- Example Grafana dashboard starter
- GitHub-ready project structure
- FSL-1.1-Apache-2.0 future license template

## Architecture

```text
Claude Code / AI coding agent
        |
        | OTLP gRPC or HTTP
        v
OpenTelemetry Collector
        |
        +--> Prometheus scrape endpoint for metrics
        +--> JSONL telemetry files for logs/traces
        |
        v
Detector / Enricher service
        |
        +--> findings.jsonl
        +--> /findings API
        +--> /metrics Prometheus endpoint
        +--> optional webhook alerts
```

This starter keeps the pipeline intentionally simple and vendor-neutral. The detector tails the collector's JSONL file output, applies rules, estimates cost where token/model fields exist, and exposes the resulting findings.

## Quick start

### 1. Start the stack

```bash
cp .env.example .env
docker compose up --build
```

Services:

| Service | URL |
|---|---|
| OTel gRPC receiver | `localhost:4317` |
| OTel HTTP receiver | `localhost:4318` |
| Collector Prometheus metrics | `localhost:8889/metrics` |
| Detector API | `http://localhost:8090` |
| Detector metrics | `http://localhost:8090/metrics` |
| Action Router API | `http://localhost:8091` |
| Action Router metrics | `http://localhost:8091/metrics` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |

Default Grafana login is `admin` / `admin`.

### 2. Configure Claude Code

In a terminal where you will run Claude Code:

```bash
source configs/claude-code/env.sh
claude
```

Or copy these variables into your shell/profile/managed settings:

```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_METRIC_EXPORT_INTERVAL=10000
export OTEL_LOGS_EXPORT_INTERVAL=5000
```

### 3. Generate activity

Use Claude Code normally. Then inspect:

```bash
curl http://localhost:8090/health
curl http://localhost:8090/findings | jq
curl http://localhost:8090/stats | jq
```

Telemetry files are written under:

```text
./data/otel/agentlens-logs.jsonl
./data/otel/agentlens-traces.jsonl
./data/findings/findings.jsonl
```


## Enforcement

AgentLens now includes optional Level 1 and Level 2 enforcement. Monitor-only remains the safest default.

Level 1 reacts to findings with audit records, generic webhooks, Slack-compatible webhooks, and optional Jira tickets. The `action-router` service tails `data/findings/findings.jsonl`, evaluates `configs/policies/enforcement.yaml`, and records actions in `data/enforcement/actions.jsonl`. Dry-run is enabled by default.

Level 2 provides CI/PR gates with `scripts/agentlens-policy-check.py`. The script exits non-zero when findings violate the configured gate, so it can block GitHub Actions or GitLab CI merges. Example workflows live under `examples/ci/` and integration notes live under `integrations/github/` and `integrations/gitlab/`.

Test enforcement locally:

```bash
bash scripts/test-enforcement.sh
curl http://localhost:8091/health
curl http://localhost:8091/actions | jq
```

See [docs/enforcement.md](docs/enforcement.md).

## Endpoint collection

For team or company deployments, use the endpoint-agent pattern:

```text
Claude Code on developer endpoint
  -> local OTel Collector agent on 127.0.0.1:4317
  -> central AgentLens collector
  -> detector/enricher
  -> dashboards/SIEM/archive
```

This lets each laptop redact locally, add endpoint/user/team attributes, queue/retry telemetry, and forward to a central collector. See [docs/endpoint-collection.md](docs/endpoint-collection.md).

Key files:

```text
configs/endpoint-agent/agent.yaml
configs/endpoint-agent/agent.env.example
configs/claude-code/env-endpoint-agent.sh
examples/endpoint-agent/docker-compose.endpoint-agent.yml
scripts/install-endpoint-agent-macos.sh
scripts/install-endpoint-agent-linux.sh
```

## Risk detections included

Initial rule packs include:

- API keys and tokens
- Private keys
- JWTs
- Database URLs
- `.env` access
- SSH key access
- AWS credential access
- Dangerous shell commands
- `curl | sh` style installers
- External network egress from shell commands
- Suspicious git activity
- Broad IAM permissions
- Public S3 and `0.0.0.0/0` IaC indicators
- MCP server/tool risk indicators
- Prompt injection phrases

Rules are plain YAML under `configs/rules/`.

## Cost monitoring

The detector tries to infer cost from common token/model fields. This is intentionally best-effort because provider attributes differ across tools and versions.

Pricing lives in:

```text
configs/pricing/anthropic.yaml
configs/pricing/openai.yaml
configs/pricing/generic.yaml
```

Keep pricing current before relying on reports for chargeback or finance.

## Security posture

This project is designed to help you avoid collecting unnecessary sensitive data:

- Prompt/body capture should be treated as sensitive.
- Use redaction rules before exporting to shared systems.
- Keep local telemetry files out of Git.
- Do not commit `.env`, findings, or telemetry data.
- Review `configs/rules/` before deploying to a team.

## Production notes

This v0.1 stack is a local/dev starter. Before production:

- Add authentication in front of the collector and detector API.
- Use TLS/mTLS for OTLP ingestion.
- Replace file export with ClickHouse, OpenSearch, Elastic, Splunk, Datadog, Axiom, Grafana Cloud, or your SIEM.
- Tune data retention.
- Decide whether prompts/outputs are allowed to be stored.
- Add team/user/repo enrichment from your IdP, GitHub/GitLab, or MDM.

## Roadmap

- v0.2: ClickHouse backend and richer dashboards
- v0.3: Splunk HEC, Elastic, OpenSearch, and S3 Security Lake exports
- v0.4: MCP server inventory and policy checks
- v0.5: Cursor/Copilot/local-agent adapters where telemetry is available
- v0.6: Runtime endpoint and gateway enforcement workflows
- v0.7: Policy-as-code budgets and advanced approval workflows


## GitHub publish quick start

```bash
git init
git add .
git commit -m "Initial AgentLens release"
git branch -M main
git remote add origin git@github.com:<your-org>/agentlens.git
git push -u origin main
```

Suggested repository description:

```text
OpenTelemetry security, DLP, spend, and endpoint visibility for AI coding agents.
```

Before publishing, review [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md), update the repository URL in examples, and replace placeholder domains/API keys in deployment docs with your own managed values.

## License

Functional Source License 1.1, Apache 2.0 Future License. See [LICENSE](LICENSE).

## Endpoint collector with tamper protection

This repo now includes a managed endpoint collector pattern for developer laptops and build servers.

Endpoint flow:

```text
Claude Code -> localhost OTLP -> endpoint OTel Collector -> central collector/detector
                              -> endpoint watchdog heartbeat/tamper events
```

Install on macOS:

```bash
sudo scripts/install-endpoint-agent-macos.sh
```

Install on Linux:

```bash
sudo OTELCOL_PATH=/usr/local/bin/otelcol-contrib scripts/install-endpoint-agent-linux.sh
```

The endpoint package includes:

- root-owned OpenTelemetry Collector config
- local OTLP listeners on `127.0.0.1:4317` and `127.0.0.1:4318`
- local redaction before telemetry leaves the endpoint
- queued/retried upstream OTLP export
- watchdog service
- collector process and port checks
- config SHA-256 checksum monitoring
- launchd/systemd auto-restart
- controlled uninstall token
- optional immutable file flags
- central tamper rules and `/endpoints` status API

Docs:

- `docs/endpoint-collection.md`
- `docs/endpoint-tamper-protection.md`

Important limitation: this is tamper-resistant and tamper-evident, not impossible to disable by a local administrator. For production, pair this with MDM and EDR controls, and alert centrally when an expected endpoint stops sending heartbeats.

## Endpoint, EDR, IdP, and cloud deployment

This repo now includes scaffolding for the full operating model:

- endpoint OTel collector agent with local redaction and tamper-evident watchdog
- EDR deployment/health/repair scaffolding for CrowdStrike, SentinelOne, Microsoft Defender, Jamf, and others
- optional IdP enrichment for Okta and JumpCloud
- static identity mapping for environments with no IdP
- AWS Terraform scaffold for ECS/ECR/S3/CloudWatch-based tests
- GCP Terraform scaffold for Artifact Registry/GCS/Cloud Run-style tests

IdP integration is **not required**. Without Okta or JumpCloud, the system uses endpoint resource attributes and optional static mappings in `configs/identity/static-identity-map.yaml`.

Start local core stack:

```bash
cp .env.example .env
docker compose up --build
```

Start with optional identity sync profile:

```bash
AGENTLENS_IDP_ENABLED=true AGENTLENS_IDP_PROVIDER=static docker compose --profile idp up --build
```

Cloud scaffolding:

```bash
cd deploy/aws/terraform && terraform init && terraform plan
cd deploy/gcp/terraform && terraform init && terraform plan -var='project_id=YOUR_GCP_PROJECT'
```

See:

- `docs/cloud-deployment.md`
- `docs/idp-integration.md`
- `integrations/edr/README.md`
- `integrations/idp/README.md`


## New backend and export options

AgentLens now includes optional backend/export scaffolding:

- ClickHouse backend config and init SQL: `docs/backend-clickhouse.md`
- Splunk HEC exporter example: `examples/exporters/splunk-hec/`
- Elastic/OpenSearch exporter example: `examples/exporters/elastic-opensearch/`
- S3 JSONL archive pattern: `examples/exporters/s3/`

Start the optional ClickHouse service for local testing:

```bash
docker compose --profile clickhouse up --build
```

## Endpoint installer and signed releases

Endpoint installer UX has been hardened with preflight checks, dry-run mode, no-start mode, upstream endpoint/API-key overrides, and optional immutable file protection.

```bash
sudo scripts/preflight-endpoint-install.sh
sudo scripts/install-endpoint-agent-macos.sh --dry-run
sudo AGENTLENS_UPSTREAM_ENDPOINT=collector.example.com:4317 scripts/install-endpoint-agent-macos.sh
```

Release helpers now generate checksums and sign release checksum files with cosign or GPG:

```bash
mkdir -p dist
git archive --format zip --output dist/agentlens-v0.1.0.zip HEAD
scripts/generate-checksums.sh dist
scripts/sign-release-artifacts.sh dist
```

See `docs/release-signing.md` and `.github/workflows/release.yml`.

## New integrations

Scaffolding has been added for:

- Cursor adapter model: `integrations/cursor/`
- local agent adapter contract: `integrations/local-agents/`
- MCP inventory/risk scoring service: `services/mcp-inventory/`
- GitHub/GitLab repo enrichment: `integrations/github/repo-enrichment.md`, `integrations/gitlab/repo-enrichment.md`
- CrowdStrike FalconPy RTR deployment scripts: `integrations/edr/crowdstrike/`
- SentinelOne RSO and STAR examples: `integrations/edr/sentinelone/`
- Microsoft Defender Advanced Hunting and Intune examples: `integrations/edr/microsoft-defender/`

Start optional MCP inventory locally:

```bash
docker compose --profile mcp up --build
curl http://localhost:8092/inventory | jq
```

## Dashboards

Grafana now includes starter dashboards for:

- overview
- spend
- endpoint health
- security findings
