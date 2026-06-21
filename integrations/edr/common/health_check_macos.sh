#!/usr/bin/env bash
set -euo pipefail
service="com.agentlens.endpoint-agent"
watchdog="com.agentlens.endpoint-watchdog"
conf="/etc/agentlens/agent.yaml"
logdir="/var/log/agentlens"

echo "AgentLens macOS health check"
launchctl print "system/${service}" >/dev/null 2>&1 && echo "collector_launchd=present" || echo "collector_launchd=missing"
launchctl print "system/${watchdog}" >/dev/null 2>&1 && echo "watchdog_launchd=present" || echo "watchdog_launchd=missing"
pgrep -af "otelcol|agentlens-endpoint" || true
test -f "${conf}" && shasum -a 256 "${conf}" || echo "config_missing=${conf}"
ls -la "${logdir}" 2>/dev/null || true
lsof -nP -iTCP:4317 -sTCP:LISTEN 2>/dev/null || true
lsof -nP -iTCP:4318 -sTCP:LISTEN 2>/dev/null || true
