# Cloud deployment

The local Docker Compose stack is for development. Production should split the system into:

- public/private OTLP ingestion endpoint
- central OTel Collector gateway
- detector/enricher service
- metrics/log storage
- object storage archive
- authentication/TLS boundary
- optional IdP sync
- optional EDR integration service

## AWS target architecture

Recommended test deployment:

```text
Endpoint agents
  -> HTTPS/gRPC OTLP endpoint behind ALB or NLB
  -> ECS Fargate OTel gateway
  -> ECS Fargate detector + identity-sync
  -> Amazon Managed Prometheus or self-hosted Prometheus
  -> CloudWatch Logs and S3 JSONL archive
  -> Grafana / Amazon Managed Grafana
  -> optional OpenSearch / Security Lake / Splunk HEC
```

Security controls:

- TLS everywhere
- API key or mTLS at the ingress layer
- WAF or CloudFront if HTTP ingress is public
- private subnets for services
- least-privilege IAM roles
- KMS-encrypted S3 and logs
- lifecycle policies for raw telemetry
- no prompts stored by default unless explicitly enabled

## GCP target architecture

Recommended test deployment:

```text
Endpoint agents
  -> HTTPS OTLP endpoint behind External HTTPS LB
  -> Cloud Run or GKE OTel gateway
  -> Cloud Run detector + identity-sync
  -> Cloud Monitoring / Managed Prometheus
  -> Cloud Logging and GCS JSONL archive
  -> Grafana or Looker Studio/BigQuery optional
```

Security controls:

- TLS on load balancer
- Cloud Armor for HTTP ingress
- Secret Manager for API keys
- CMEK where required
- private service networking where possible
- GCS retention and lifecycle policies

## Important

Do not expose unauthenticated OTLP endpoints to the internet. Endpoint agents can generate a high cardinality and potentially sensitive data stream. Use TLS, auth, rate limits, and redaction at the endpoint.
