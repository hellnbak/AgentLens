#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/findings data/enforcement
cat >> data/findings/findings.jsonl <<'EOF'
{"finding_id":"test-secret-001","ts":1760000000,"rule_id":"secret.aws_access_key","category":"secrets","severity":"critical","risk_score":95,"description":"Synthetic test secret finding","match":"AKIA...[REDACTED]...MPLE","context":{"repo":"hellnbak/agentlens","identity.email":"test@example.com"},"estimated_cost_usd":0,"record_hash":"test"}
EOF

python3 scripts/agentlens-policy-check.py --policy configs/policies/enforcement.yaml --findings-file data/findings/findings.jsonl --gate pull_request --format text || true

echo "Expected: policy check reports one violation. In CI, omit '|| true' to fail the job."
