# Release signing and checksums

AgentLens releases should publish:

- source archive
- endpoint package archive
- `SHA256SUMS`
- `SHA256SUMS.sig` from cosign, or `SHA256SUMS.asc` from GPG

Build locally:

```bash
mkdir -p dist
git archive --format zip --output dist/agentlens-v0.1.0.zip HEAD
scripts/generate-checksums.sh dist
scripts/sign-release-artifacts.sh dist
```

GitHub release tags trigger `.github/workflows/release.yml`.
