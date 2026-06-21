# JumpCloud example: macOS endpoint deployment

Use a JumpCloud command to deploy the endpoint collector package to managed Macs.

Example command body:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /tmp
curl -L -o agentlens.zip https://example.com/releases/agentlens.zip
rm -rf agentlens
unzip -q agentlens.zip
cd agentlens
sudo scripts/install-endpoint-agent-macos.sh
sudo /usr/bin/sed -i '' 's#otel-gateway.example.com:4317#otel-gateway.yourcompany.com:4317#g' /etc/agentlens/agent.env
sudo /usr/bin/sed -i '' 's#replace-with-enrollment-or-collector-key#YOUR_MANAGED_KEY#g' /etc/agentlens/agent.env
sudo launchctl kickstart -k system/com.agentlens.endpoint-agent
sudo launchctl kickstart -k system/com.agentlens.endpoint-watchdog
```

Use JumpCloud variables or a secrets workflow for the API key instead of hard-coding it.
