#!/usr/bin/env bash
set -euo pipefail
: "${AGENTLENS_S3_BUCKET:?set AGENTLENS_S3_BUCKET}"
PREFIX="${AGENTLENS_S3_PREFIX:-agentlens/otel}"
aws s3 sync /var/lib/agentlens/s3-buffer "s3://${AGENTLENS_S3_BUCKET}/${PREFIX}/$(date -u +%Y/%m/%d)/" --only-show-errors
