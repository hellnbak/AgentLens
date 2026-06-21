# ClickHouse backend

ClickHouse is optional and useful for large telemetry volumes and long-running cost/security analytics.

Start ClickHouse next to the local stack:

```bash
docker compose -f docker-compose.yml -f examples/clickhouse/docker-compose.clickhouse.yml up --build
```

Then point the collector at `configs/otel-collector/collector-clickhouse.yaml` or merge the ClickHouse exporter into your production collector config.
