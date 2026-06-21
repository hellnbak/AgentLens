#!/usr/bin/env bash
set -euo pipefail
launchctl list | grep -q com.agentlens.endpoint-agent
launchctl list | grep -q com.agentlens.endpoint-watchdog
/usr/local/bin/agentlens-endpoint-watchdog --once
