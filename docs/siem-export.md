# SIEM export

v0.1 writes findings to JSONL and exposes them through an API. That keeps exports simple.

## JSONL findings

```text
data/findings/findings.jsonl
```

## API

```bash
curl http://localhost:8090/findings
curl http://localhost:8090/stats
```

## Webhook alerts

Set these in `.env`:

```bash
AGENTLENS_WEBHOOK_URL=https://example.com/webhook
AGENTLENS_MIN_ALERT_RISK=75
```

## Production export ideas

- Splunk HEC
- Elastic/OpenSearch bulk API
- S3 JSONL partitioned by date
- AWS Security Lake custom source
- Datadog logs intake
- Axiom datasets
- Grafana Loki
