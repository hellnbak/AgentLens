# Intune/Linux remediation example

Detection script idea:

```bash
#!/usr/bin/env bash
systemctl is-active --quiet agentlens-endpoint-agent.service || exit 1
systemctl is-active --quiet agentlens-endpoint-watchdog.service || exit 1
nc -z 127.0.0.1 4317 || exit 1
exit 0
```

Remediation script idea:

```bash
#!/usr/bin/env bash
systemctl restart agentlens-endpoint-agent.service || true
systemctl restart agentlens-endpoint-watchdog.service || true
```
