# Terraform configuration for MSME Retail Intelligence System
# FREE TIER OPTIMIZED

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "MSME-Retail-Intelligence"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"  # Mumbai - free tier eligible
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "msme-retail-intelligence"
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Outputs
output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.main.id
}

output "dynamodb_tables" {
  description = "DynamoDB table names"
  value = {
    stores         = aws_dynamodb_table.stores.name
    uploads        = aws_dynamodb_table.uploads.name
    extracted_data = aws_dynamodb_table.extracted_data.name
  }
}

output "lambda_functions" {
  description = "Lambda function names"
  value = {
    upload_handler    = aws_lambda_function.upload_handler.function_name
    extraction_worker = aws_lambda_function.extraction_worker.function_name
  }
}

output "api_gateway_url" {
  description = "API Gateway invoke URL"
  value       = "${aws_api_gateway_deployment.main.invoke_url}/${var.environment}"
}
