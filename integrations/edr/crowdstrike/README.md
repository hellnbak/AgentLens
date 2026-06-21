# CrowdStrike Falcon integration

Use Falcon RTR for deployment, health checks, repair, and log collection.

## Suggested RTR workflows

- install endpoint collector
- run health check
- restart collector/watchdog
- pull `/var/log/agentlens/*.log`
- verify config checksum
- repair missing launchd/systemd service

## Required secrets

```text
FALCON_CLIENT_ID=
FALCON_CLIENT_SECRET=
FALCON_CLOUD=us-1|us-2|eu-1|gov1
```

The Python files are intentionally dry-run first. Set `--execute` when you are ready to run RTR commands.
