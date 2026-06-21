# SentinelOne STAR rule guidance

Create STAR rules for these patterns:

- process termination of `otelcol`, `otelcol-contrib`, or `agentlens-endpoint-watchdog`
- modification/deletion of `/etc/agentlens/agent.yaml`
- `launchctl unload` or `systemctl disable` involving AgentLens services
- network block or repeated connection failures to central collector

Suggested response actions:

- alert only for first occurrence
- run remediation script for service stopped/config mismatch
- escalate repeated tamper to incident workflow
