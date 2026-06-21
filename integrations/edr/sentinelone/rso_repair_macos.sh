#!/usr/bin/env bash
set -euo pipefail
launchctl kickstart -k system/com.agentlens.endpoint-agent || true
launchctl kickstart -k system/com.agentlens.endpoint-watchdog || true
/usr/local/bin/agentlens-endpoint-watchdog --once
