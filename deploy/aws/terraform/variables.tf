variable "project" { type = string default = "agentlens" }
variable "region" { type = string default = "us-east-1" }
variable "environment" { type = string default = "test" }
variable "allowed_otlp_cidrs" { type = list(string) default = ["0.0.0.0/0"] }
