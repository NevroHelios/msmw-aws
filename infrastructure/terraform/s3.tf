# S3 Bucket for file storage
# FREE TIER: 5GB storage for 12 months

resource "aws_s3_bucket" "main" {
  bucket = "${var.project_name}-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name = "MSME Retail Intelligence Storage"
  }
}

# Enable versioning (optional)
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  
  versioning_configuration {
    status = "Disabled"  # Keep disabled for free tier
  }
}

# Bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"  # Free encryption
    }
  }
}

# Block public access (security)
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CORS configuration for frontend uploads
resource "aws_s3_bucket_cors_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["*"]  # Restrict in production
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Lifecycle policy to save costs
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  
  rule {
    id     = "delete-old-processed"
    status = "Enabled"
    
    filter {
      prefix = "processed/"
    }
    
    expiration {
      days = 90  # Delete processed files after 90 days
    }
  }
  
  rule {
    id     = "archive-old-raw"
    status = "Enabled"
    
    filter {
      prefix = "raw/"
    }
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"  # Move to cheaper storage after 30 days
    }
  }
}
