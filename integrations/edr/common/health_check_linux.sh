#!/usr/bin/env bash
set -euo pipefail
service="agentlens-endpoint-agent.service"
watchdog="agentlens-endpoint-watchdog.service"
conf="/etc/agentlens/agent.yaml"
logdir="/var/log/agentlens"

echo "AgentLens Linux health check"
systemctl is-enabled "${service}" || true
systemctl is-active "${service}" || true
systemctl is-enabled "${watchdog}" || true
systemctl is-active "${watchdog}" || true
pgrep -af "otelcol|agentlens-endpoint" || true
test -f "${conf}" && sha256sum "${conf}" || echo "config_missing=${conf}"
ls -la "${logdir}" 2>/dev/null || true
ss -ltnp 2>/dev/null | grep -E ':(4317|4318)\b' || true
