#!/usr/bin/env bash
set -euo pipefail

# Controlled uninstall for macOS endpoint collector.
# Requires AGENTLENS_UNINSTALL_TOKEN to match /etc/agentlens/agent.env.

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run with sudo." >&2
  exit 1
fi

ENV_FILE="/etc/agentlens/agent.env"
EXPECTED="$(grep '^AGENTLENS_UNINSTALL_TOKEN=' "${ENV_FILE}" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)"
PROVIDED="${AGENTLENS_UNINSTALL_TOKEN:-}"

if [[ -z "${EXPECTED}" || "${EXPECTED}" == "change-me-long-random-token" || "${PROVIDED}" != "${EXPECTED}" ]]; then
  echo "Uninstall denied. Provide the managed uninstall token:" >&2
  echo "  sudo AGENTLENS_UNINSTALL_TOKEN=<token> $0" >&2
  exit 2
fi

for f in /etc/agentlens/agent.yaml /etc/agentlens/agent.yaml.sha256 /Library/LaunchDaemons/com.agentlens.endpoint-agent.plist /Library/LaunchDaemons/com.agentlens.endpoint-watchdog.plist; do
  chflags nouchg "$f" >/dev/null 2>&1 || true
done

launchctl bootout system /Library/LaunchDaemons/com.agentlens.endpoint-watchdog.plist >/dev/null 2>&1 || true
launchctl bootout system /Library/LaunchDaemons/com.agentlens.endpoint-agent.plist >/dev/null 2>&1 || true
rm -f /Library/LaunchDaemons/com.agentlens.endpoint-agent.plist /Library/LaunchDaemons/com.agentlens.endpoint-watchdog.plist
rm -f /usr/local/bin/agentlens-endpoint-agent /usr/local/bin/agentlens-endpoint-watchdog
rm -rf /etc/agentlens

echo "Uninstalled agentlens endpoint collector. Logs remain in /var/log/agentlens for audit retention."
