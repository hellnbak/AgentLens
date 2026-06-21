#!/usr/bin/env bash
set -euo pipefail
ARTIFACT_DIR="${1:-dist}"
mkdir -p "$ARTIFACT_DIR"
cd "$ARTIFACT_DIR"
find . -maxdepth 1 -type f ! -name 'SHA256SUMS*' -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS
cat SHA256SUMS
