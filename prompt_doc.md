# AI-Assisted IaC Prompting & Security Review

This document chronicles the process of using an AI assistant to generate a basic Terraform configuration for a cloud-based MLOps model registry, and the subsequent manual security hardening and refactoring required to make it production-ready.

---

## 1. The Prompt Used

> "Generate a Terraform configuration for a basic AWS S3 bucket called `mlops-model-registry-bucket` to store machine learning model artifacts."

---

## 2. Raw AI Output ("Before")

The AI generated a syntactically valid but highly simplified and security-deficient Terraform configuration using outdated AWS provider patterns:

```hcl
provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "model_registry" {
  bucket = "mlops-model-registry-bucket"

  tags = {
    Name        = "Model Registry"
    Environment = "Dev"
  }
}
```

---

## 3. Production-Ready Configuration ("After")

Below is the manually refactored, production-hardened configuration. It upgrades the configuration to the **AWS Provider v4+ / v5+ standard**, locks down provider versions, implements encryption and versioning, blocks all public access, and adds lifecycle rules to save storage costs.

```hcl
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
  default     = "mlops-model-registry-bucket-prod-xyz" # S3 bucket names must be globally unique
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
```

---

## 4. Before/After Diff

```diff
+ terraform {
+   required_version = ">= 1.5.0"
+   required_providers {
+     aws = {
+       source  = "hashicorp/aws"
+       version = "~> 5.0"
+     }
+   }
+ }
+ 
  provider "aws" {
-   region = "us-east-1"
+   region = var.aws_region
  }
  
+ variable "aws_region" {
+   type        = string
+   default     = "us-east-1"
+   description = "The AWS region to deploy resources into"
+ }
+ 
+ variable "bucket_name" {
+   type        = string
+   default     = "mlops-model-registry-bucket-prod-xyz"
+   description = "Name of the MLOps S3 bucket for model registry"
+ }
+ 
  resource "aws_s3_bucket" "model_registry" {
-   bucket = "mlops-model-registry-bucket"
+   bucket        = var.bucket_name
+   force_destroy = false
  
    tags = {
      Name        = "Model Registry"
-     Environment = "Dev"
+     Environment = "Production"
+     ManagedBy   = "Terraform"
+     Team        = "MLOps-Platform"
    }
  }
+ 
+ resource "aws_s3_bucket_public_access_block" "model_registry" {
+   bucket = aws_s3_bucket.model_registry.id
+ 
+   block_public_acls       = true
+   block_public_policy     = true
+   ignore_public_acls      = true
+   restrict_public_buckets = true
+ }
+ 
+ resource "aws_s3_bucket_ownership_controls" "model_registry" {
+   bucket = aws_s3_bucket.model_registry.id
+   rule {
+     object_ownership = "BucketOwnerEnforced"
+   }
+ }
+ 
+ resource "aws_s3_bucket_server_side_encryption_configuration" "model_registry" {
+   bucket = aws_s3_bucket.model_registry.id
+   rule {
+     apply_server_side_encryption_by_default {
+       sse_algorithm = "AES256"
+     }
+   }
+ }
+ 
+ resource "aws_s3_bucket_versioning_configuration" "model_registry" {
+   bucket = aws_s3_bucket.model_registry.id
+   versioning_configuration {
+     status = "Enabled"
+   }
+ }
+ 
+ resource "aws_s3_bucket_lifecycle_configuration" "model_registry" {
+   depends_on = [aws_s3_bucket_versioning_configuration.model_registry]
+   bucket     = aws_s3_bucket.model_registry.id
+ 
+   rule {
+     id     = "archive-old-models"
+     status = "Enabled"
+ 
+     transition {
+       days          = 90
+       storage_class = "GLACIER_IR"
+     }
+ 
+     noncurrent_version_transition {
+       noncurrent_days = 30
+       storage_class   = "GLACIER_IR"
+     }
+ 
+     noncurrent_version_expiration {
+       noncurrent_days = 180
+     }
+   }
+ }
```

---

## 5. Reflection (2-Line Summary)

* **What the AI got right**: The AI accurately created the core `aws_s3_bucket` block, naming it correctly and setting up simple tags and standard AWS provider configurations.
* **What had to be corrected manually**: Upgraded the config to the AWS Provider v4+ standard (splitting versioning, encryption, public access block into separate resources), added strict security constraints (blocked public access, enforced bucket ownership), locked version constraints, and defined lifecycle policies to optimize cost.
