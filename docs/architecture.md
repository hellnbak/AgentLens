# Architecture

AgentLens is intentionally collector-first.

1. AI coding platforms emit OTel telemetry.
2. The OTel Collector receives OTLP over gRPC/HTTP.
3. The collector applies basic redaction and resource attribution.
4. Metrics are exposed to Prometheus.
5. Logs and traces are exported to local JSONL files.
6. The detector service tails those files, applies rules, estimates spend, and emits findings.

This architecture avoids lock-in and makes it easy to replace the local file exporter with production systems such as ClickHouse, OpenSearch, Elastic, Splunk, Datadog, Axiom, Grafana Cloud, Loki, or S3.

## Why file export in v0.1?

File export keeps the MVP easy to run and inspect. It also avoids requiring a paid backend or a heavy local datastore on day one.

## Production direction

For production, move from local files to a durable backend and add:

- TLS/mTLS
- authentication
- role-based access
- retention controls
- prompt/body storage decisions
- SIEM forwarding
- team/user/repo enrichment
