#!/usr/bin/env bash
# Source this file before running Claude Code:
#   source configs/claude-code/env.sh
#   claude

export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:4317}
export OTEL_METRIC_EXPORT_INTERVAL=${OTEL_METRIC_EXPORT_INTERVAL:-10000}
export OTEL_LOGS_EXPORT_INTERVAL=${OTEL_LOGS_EXPORT_INTERVAL:-5000}

# Optional resource attribution. Override these in your shell/MDM as needed.
export OTEL_SERVICE_NAME=${OTEL_SERVICE_NAME:-claude-code}
export OTEL_RESOURCE_ATTRIBUTES=${OTEL_RESOURCE_ATTRIBUTES:-deployment.environment=local,ai.dev.platform=claude_code}

echo "Claude Code telemetry enabled. OTLP endpoint: ${OTEL_EXPORTER_OTLP_ENDPOINT}"
