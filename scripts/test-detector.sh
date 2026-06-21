#!/usr/bin/env bash
set -euo pipefail
mkdir -p data/otel data/findings
cat examples/sample-telemetry/secret-event.json >> data/otel/agentlens-logs.jsonl
sleep 2
curl -s http://localhost:8090/findings | jq
