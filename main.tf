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
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "The AWS region to deploy resources into"
}

variable "bucket_name" {
  type        = string
  default     = "mlops-model-registry-bucket-prod-xyz"
  description = "Name of the MLOps S3 bucket for model registry"
}

# 1. Main S3 Bucket Resource
resource "aws_s3_bucket" "model_registry" {
  bucket        = var.bucket_name
  force_destroy = false # Prevent accidental deletion of models

  tags = {
    Name        = "Model Registry"
    Environment = "Production"
    ManagedBy   = "Terraform"
    Team        = "MLOps-Platform"
  }
}

# 2. Block all Public Access (Security Best Practice)
resource "aws_s3_bucket_public_access_block" "model_registry" {
  bucket = aws_s3_bucket.model_registry.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 3. Bucket Ownership Controls
resource "aws_s3_bucket_ownership_controls" "model_registry" {
  bucket = aws_s3_bucket.model_registry.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# 4. Enable Server-Side Encryption (SSE-S3)
resource "aws_s3_bucket_server_side_encryption_configuration" "model_registry" {
  bucket = aws_s3_bucket.model_registry.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 5. Enable Versioning (Crucial for rollback and audits of model weights)
resource "aws_s3_bucket_versioning_configuration" "model_registry" {
  bucket = aws_s3_bucket.model_registry.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 6. Lifecycle Management (Transition old/non-current model versions to Glacier)
resource "aws_s3_bucket_lifecycle_configuration" "model_registry" {
  depends_on = [aws_s3_bucket_versioning_configuration.model_registry]
  bucket     = aws_s3_bucket.model_registry.id

  rule {
    id     = "archive-old-models"
    status = "Enabled"

    # Transition active models older than 90 days to Glacier Instant Retrieval
    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }

    # Transition noncurrent versions (previous iterations of models) to Glacier after 30 days
    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER_IR"
    }

    # Clean up noncurrent model versions after 180 days
    noncurrent_version_expiration {
      noncurrent_days = 180
    }
  }
}
