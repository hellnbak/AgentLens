# AWS deployment scaffold

This Terraform scaffold creates the basic AWS building blocks for a test deployment:

- VPC and subnets
- ECS cluster
- ECR repositories
- S3 archive bucket
- CloudWatch log groups
- IAM roles
- security groups
- placeholders for ALB/NLB and services

It is intentionally conservative and incomplete for production. Add your domain, TLS certificate, WAF, mTLS/API gateway, and backend storage choices before internet exposure.

## Usage

```bash
cd deploy/aws/terraform
terraform init
terraform plan -var='project=agentlens' -var='region=us-east-1'
terraform apply
```

Then build and push images to the generated ECR repos.
