# Endpoint collector tamper protection

The endpoint collector is designed to be **tamper-resistant and tamper-evident**, not magically tamper-proof. On any developer laptop where the user has local admin/root, they can eventually disable local software. The goal is to make disablement hard, require elevated privileges, and create a central alert when it happens.

## Components

Each managed endpoint runs two services:

1. `agentlens-endpoint-agent`
   - OpenTelemetry Collector Contrib
   - Listens on `127.0.0.1:4317` and `127.0.0.1:4318`
   - Receives Claude Code telemetry locally
   - Redacts obvious secrets locally
   - Adds endpoint metadata
   - Queues and forwards telemetry upstream
   - Tails watchdog heartbeat events and forwards them upstream

2. `agentlens-endpoint-watchdog`
   - Python watchdog service
   - Checks collector process state
   - Checks OTLP listener ports
   - Checks service manager state
   - Checks collector config SHA-256 checksum
   - Emits heartbeat/tamper events to `/var/log/agentlens/endpoint-watchdog.jsonl`
   - Attempts to restart the collector when unhealthy

## macOS protections

The macOS installer creates root-owned launch daemons:

- `/Library/LaunchDaemons/com.agentlens.endpoint-agent.plist`
- `/Library/LaunchDaemons/com.agentlens.endpoint-watchdog.plist`

It also creates root-owned config under:

- `/etc/agentlens/agent.yaml`
- `/etc/agentlens/agent.env`
- `/etc/agentlens/agent.yaml.sha256`

Launchd is configured with `RunAtLoad` and `KeepAlive`.

Optional immutable mode:

```bash
sudo AGENTLENS_ENABLE_IMMUTABLE=true scripts/install-endpoint-agent-macos.sh
```

This applies `chflags uchg` to important files. Your MDM workflow must clear the flag before upgrades:

```bash
sudo chflags nouchg /etc/agentlens/agent.yaml /etc/agentlens/agent.yaml.sha256 \
  /Library/LaunchDaemons/com.agentlens.endpoint-agent.plist \
  /Library/LaunchDaemons/com.agentlens.endpoint-watchdog.plist
```

## Linux protections

The Linux installer creates systemd services:

- `agentlens-endpoint-agent.service`
- `agentlens-endpoint-watchdog.service`

The services use:

- `Restart=always`
- `NoNewPrivileges=true`
- `ProtectSystem=full`
- `ProtectHome=read-only`
- root-owned config under `/etc/agentlens`

Optional immutable mode:

```bash
sudo AGENTLENS_ENABLE_IMMUTABLE=true scripts/install-endpoint-agent-linux.sh
```

This applies `chattr +i` to important files. Your management workflow must clear it before upgrades:

```bash
sudo chattr -i /etc/agentlens/agent.yaml /etc/agentlens/agent.yaml.sha256 \
  /etc/systemd/system/agentlens-endpoint-agent.service \
  /etc/systemd/system/agentlens-endpoint-watchdog.service
```

## Central tamper findings

The watchdog emits JSON heartbeat records with event type:

```text
agentlens.endpoint_heartbeat
```

The collector tails those events and forwards them upstream. The central detector includes rules for:

- `collector_process_not_found`
- `collector_otlp_grpc_not_listening`
- `collector_service_inactive`
- `watchdog_service_inactive`
- `collector_config_checksum_mismatch`
- `collector_config_missing`
- `expected_checksum_missing`

The detector exposes endpoint status at:

```text
http://localhost:8090/endpoints
```

Any endpoint that stops sending heartbeats should be treated as stale. In production, create a scheduled job or SIEM correlation rule that alerts when an enrolled endpoint has not sent a heartbeat for 5-10 minutes.

## Controlled uninstall

The uninstall scripts require `AGENTLENS_UNINSTALL_TOKEN` to match the managed value in `/etc/agentlens/agent.env`.

macOS:

```bash
sudo AGENTLENS_UNINSTALL_TOKEN='<token>' scripts/uninstall-endpoint-agent-macos.sh
```

Linux:

```bash
sudo AGENTLENS_UNINSTALL_TOKEN='<token>' scripts/uninstall-endpoint-agent-linux.sh
```

This is not a cryptographic anti-admin guarantee. It is intended to prevent casual removal and support MDM-driven authorized uninstall.

## Recommended enterprise deployment

Use device management to deploy and enforce the endpoint agent:

- Jamf, Kandji, Mosyle, or JumpCloud for macOS
- Intune, Fleet, Ansible, Puppet, Chef, or Salt for Linux
- Cloudflare Zero Trust, VPN, or mTLS for upstream transport
- Per-device or per-user API keys
- Central inventory of expected endpoints
- SIEM alerts for stale endpoints and tamper events

For stronger protection, pair this with EDR controls:

- alert on service stop/disable events
- protect `/etc/agentlens`, LaunchDaemon, and systemd unit paths
- block non-admin edits to shell profiles that remove Claude Code telemetry env vars
- detect unusual network blocking to the collector gateway
