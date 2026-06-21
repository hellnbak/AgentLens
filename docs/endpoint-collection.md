# Endpoint collection

Endpoint collection is the production-friendly deployment model for AgentLens.

Instead of every developer laptop sending Claude Code telemetry directly to a public collector, each endpoint runs a small local OpenTelemetry Collector agent. Claude Code talks to `localhost`; the agent enriches, redacts, queues, retries, and forwards telemetry to your central collector.

## Why use an endpoint agent?

Benefits:

- Keeps Claude Code configuration simple: always send OTLP to `127.0.0.1:4317`.
- Adds endpoint identity, user, team, environment, and device attributes.
- Redacts obvious secrets before telemetry leaves the laptop.
- Buffers and retries when the developer is offline or on a bad network.
- Avoids exposing the central collector directly to every local process.
- Lets you manage configuration with MDM, Jamf, Intune, JumpCloud, Chef, Ansible, or scripts.

## Deployment pattern

```text
Claude Code on laptop
  -> localhost:4317 / localhost:4318
  -> Endpoint OTel Collector agent
  -> central OTLP gateway
  -> detector/enricher
  -> dashboards/SIEM/archive
```

## Local test

Terminal 1, start the central stack:

```bash
cp .env.example .env
docker compose up --build
```

Terminal 2, start an endpoint agent in Docker:

```bash
cd examples/endpoint-agent
docker compose -f docker-compose.endpoint-agent.yml up
```

Terminal 3, point Claude Code at the endpoint agent:

```bash
source configs/claude-code/env-endpoint-agent.sh
claude
```

For local testing, the endpoint agent forwards to `localhost:4317`, which is the central collector from this repo's Docker Compose stack.

## macOS endpoint install

For developer Macs, install the collector with Homebrew and run it under launchd:

```bash
sudo scripts/install-endpoint-agent-macos.sh
```

Then edit the LaunchDaemon or managed environment values so these are correct for your org:

```text
AGENTLENS_UPSTREAM_ENDPOINT=otel-gateway.example.com:4317
AGENTLENS_UPSTREAM_INSECURE=false
AGENTLENS_ENDPOINT_ID=<serial-or-mdm-device-id>
AGENTLENS_API_KEY=<collector-api-key-if-used>
OTEL_RESOURCE_ATTRIBUTES=team=security,user.email=steve@example.com,device.owner=steve,deployment.environment=prod
```

## Linux endpoint install

Install `otelcol-contrib`, then:

```bash
sudo scripts/install-endpoint-agent-linux.sh
```

Update `/etc/agentlens/agent.env` with your central collector endpoint and attributes:

```bash
sudo vi /etc/agentlens/agent.env
sudo systemctl restart agentlens-endpoint-agent
```

## Claude Code endpoint environment

Claude Code only needs to know about the local endpoint agent:

```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_TRACES_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317
export OTEL_METRIC_EXPORT_INTERVAL=10000
export OTEL_LOGS_EXPORT_INTERVAL=5000
```

For managed deployments, push these through shell profile management, MDM, developer bootstrap scripts, or Claude Code managed settings where appropriate.

## Central collector exposure

For a real deployment, do not leave the central collector unauthenticated on the internet.

Recommended options:

1. Put the central collector behind a private VPN, Zero Trust tunnel, or internal network.
2. Terminate TLS at a reverse proxy or load balancer.
3. Require an API key, mTLS, or OIDC-aware proxy before traffic reaches the collector.
4. Use separate collector endpoints for dev/test/prod.
5. Rate-limit and log endpoint IDs.

## Identity and enrichment

Minimum recommended endpoint attributes:

```text
endpoint.id
host.name
os.type
user.email
team
device.owner
deployment.environment
ai.dev.platform
repo.name, when available
```

Some fields come from the collector's resource detection. Others should be injected using `OTEL_RESOURCE_ATTRIBUTES` from MDM or developer tooling.

## Privacy model

Endpoint telemetry can contain sensitive data. The safest model is:

- Redact on the endpoint before forwarding.
- Store prompts/outputs only when explicitly allowed.
- Store security findings longer than raw telemetry.
- Keep local spool/log files small and rotated.
- Do not send telemetry to third-party systems until DLP rules have run.

## Failure behavior

The endpoint agent uses sending queues and retry-on-failure. If the endpoint is offline, telemetry may be buffered briefly in memory. This starter does not enable long-term disk-backed buffering; add persistent queues before relying on guaranteed delivery.

## Files added for endpoint collection

```text
configs/endpoint-agent/agent.yaml
configs/endpoint-agent/agent.env.example
configs/claude-code/env-endpoint-agent.sh
examples/endpoint-agent/docker-compose.endpoint-agent.yml
scripts/install-endpoint-agent-macos.sh
scripts/install-endpoint-agent-linux.sh
```

## Hardened endpoint package

Use the hardened config by default:

```text
configs/endpoint-agent/agent-secure.yaml
```

This config receives Claude Code telemetry locally, tails watchdog heartbeat/tamper events, applies endpoint-side redaction, adds endpoint metadata, queues/retries, and forwards upstream.

The installer copies this config to:

```text
/etc/agentlens/agent.yaml
```

The watchdog writes heartbeats to:

```text
/var/log/agentlens/endpoint-watchdog.jsonl
```

The endpoint collector tails that file and forwards heartbeat/tamper records upstream. The central detector exposes enrolled/seen endpoints at:

```text
/endpoints
```

See `docs/endpoint-tamper-protection.md` for hardening details.
