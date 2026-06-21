output "ecs_cluster_name" { value = aws_ecs_cluster.this.name }
output "collector_ecr_repo" { value = aws_ecr_repository.collector.repository_url }
output "detector_ecr_repo" { value = aws_ecr_repository.detector.repository_url }
output "identity_sync_ecr_repo" { value = aws_ecr_repository.identity_sync.repository_url }
output "archive_bucket" { value = aws_s3_bucket.archive.bucket }
output "vpc_id" { value = aws_vpc.this.id }
output "public_subnet_ids" { value = [for s in aws_subnet.public : s.id] }
