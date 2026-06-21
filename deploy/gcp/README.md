# GCP deployment scaffold

This Terraform scaffold creates basic GCP resources for test deployments:

- Artifact Registry repositories
- GCS archive bucket
- service accounts
- Cloud Run placeholders
- log/monitoring API enablement

Add your HTTPS load balancer, Cloud Armor, Serverless NEG, Secret Manager values, and Cloud Run service definitions before production.

## Usage

```bash
cd deploy/gcp/terraform
terraform init
terraform plan -var='project_id=my-project' -var='region=us-central1'
terraform apply
```
