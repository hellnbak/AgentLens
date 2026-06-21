# Optional IdP integration

AgentLens can run with no IdP at all. In that mode endpoint identity comes from local resource attributes such as hostname, username, email, device serial, repository, and team values deployed by MDM or environment variables.

IdP integration is optional and adds enrichment:

- map `user.email` to department, manager, cost center, employment status, and groups
- map device owners to teams
- disable or flag telemetry from inactive users
- add SSO for the central UI/API when a UI is added
- improve budgets and spend reporting by team or cost center

Supported scaffolding:

- Okta: SCIM-style user/group enrichment plus API token based sync
- JumpCloud: user/group/device enrichment using API key and org ID
- Static CSV/YAML mapping: no external IdP required

## Operating without an IdP

Use `configs/identity/static-identity-map.yaml` and endpoint resource attributes:

```bash
export OTEL_RESOURCE_ATTRIBUTES="user.email=alice@example.com,team=engineering,cost_center=ENG,device.owner=alice"
```

The central detector will still process telemetry, costs, DLP events, and endpoint health.

## Recommended production pattern

1. Keep endpoint collection independent of IdP availability.
2. Sync IdP metadata periodically into a local cache.
3. Enrich telemetry from the local cache only.
4. If IdP sync fails, continue using last-known-good identity mappings.
5. Never block telemetry ingestion because identity enrichment is unavailable.

## Environment variables

```text
AGENTLENS_IDP_ENABLED=false
AGENTLENS_IDP_PROVIDER=static|okta|jumpcloud
AGENTLENS_IDENTITY_MAP=/app/identity/static-identity-map.yaml

# Okta optional
OKTA_ORG_URL=https://example.okta.com
OKTA_API_TOKEN=

# JumpCloud optional
JUMPCLOUD_API_KEY=
JUMPCLOUD_ORG_ID=
```
