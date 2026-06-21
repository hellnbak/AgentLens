# SentinelOne STAR rule examples

Create STAR rules for:

- `agentlens-endpoint-agent` process terminated repeatedly
- `/etc/agentlens/agent.yaml` modified outside approved updater
- `com.agentlens.endpoint-agent.plist` unloaded or deleted on macOS
- `agentlens-endpoint-agent.service` disabled/stopped on Linux
- Claude/Cursor/local agent process observed while AgentLens heartbeat missing

Recommended response: alert first, then run RSO repair script after validation.
