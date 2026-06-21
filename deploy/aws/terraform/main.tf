terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" { region = var.region }

data "aws_availability_zones" "available" {}

locals {
  name = "${var.project}-${var.environment}"
  azs  = slice(data.aws_availability_zones.available.names, 0, 2)
}

resource "aws_vpc" "this" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = local.name }
}

resource "aws_subnet" "public" {
  for_each                = toset(local.azs)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(aws_vpc.this.cidr_block, 8, index(local.azs, each.key))
  availability_zone       = each.key
  map_public_ip_on_launch = true
  tags = { Name = "${local.name}-public-${each.key}" }
}

resource "aws_internet_gateway" "this" { vpc_id = aws_vpc.this.id tags = { Name = local.name } }

resource "aws_route_table" "public" { vpc_id = aws_vpc.this.id tags = { Name = "${local.name}-public" } }
resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}
resource "aws_route_table_association" "public" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_ecs_cluster" "this" { name = local.name }

resource "aws_ecr_repository" "collector" {
  name                 = "${local.name}/collector"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}
resource "aws_ecr_repository" "detector" {
  name                 = "${local.name}/detector"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}
resource "aws_ecr_repository" "identity_sync" {
  name                 = "${local.name}/identity-sync"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_s3_bucket" "archive" { bucket_prefix = "${local.name}-archive-" }
resource "aws_s3_bucket_server_side_encryption_configuration" "archive" {
  bucket = aws_s3_bucket.archive.id
  rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } }
}
resource "aws_s3_bucket_public_access_block" "archive" {
  bucket = aws_s3_bucket.archive.id
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}

resource "aws_cloudwatch_log_group" "collector" { name = "/${local.name}/collector" retention_in_days = 30 }
resource "aws_cloudwatch_log_group" "detector" { name = "/${local.name}/detector" retention_in_days = 30 }

resource "aws_security_group" "otlp_ingress" {
  name        = "${local.name}-otlp-ingress"
  description = "OTLP ingress - restrict this before production"
  vpc_id      = aws_vpc.this.id
  ingress { from_port = 4317 to_port = 4318 protocol = "tcp" cidr_blocks = var.allowed_otlp_cidrs }
  egress  { from_port = 0 to_port = 0 protocol = "-1" cidr_blocks = ["0.0.0.0/0"] }
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "${local.name}-ecs-task-execution"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }] })
}
resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
