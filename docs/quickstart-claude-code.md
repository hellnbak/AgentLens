# Claude Code quickstart

## Start AgentLens

```bash
cp .env.example .env
docker compose up --build
```

## Enable Claude Code telemetry

```bash
source configs/claude-code/env.sh
claude
```

The helper exports:

```bash
CLAUDE_CODE_ENABLE_TELEMETRY=1
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## Validate

```bash
curl http://localhost:8090/health | jq
curl http://localhost:8090/stats | jq
```

Open Grafana at `http://localhost:3000`.
