# IdP integrations

IdP support is optional. The project runs with static identity enrichment or no enrichment.

Integrations included as scaffolding:

- Okta API token sync
- JumpCloud API key sync
- static YAML mapping

Do not put IdP tokens in repo files. Use environment variables, AWS Secrets Manager, GCP Secret Manager, Kubernetes Secrets, or your secret store.
