# Lambda Functions
# FREE TIER: 1M requests/month (always free) + 400,000 GB-seconds

# Note: Lambda deployment packages must be created first
# Run: ./scripts/package_lambda.sh before applying terraform

# Upload Handler Lambda
resource "aws_lambda_function" "upload_handler" {
  filename         = "../../lambda_packages/upload_handler.zip"
  function_name    = "${var.project_name}-upload-handler"
  role             = aws_iam_role.upload_handler.arn
  handler          = "handler.lambda_handler"
  source_code_hash = fileexists("../../lambda_packages/upload_handler.zip") ? filebase64sha256("../../lambda_packages/upload_handler.zip") : ""
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      S3_BUCKET_NAME         = aws_s3_bucket.main.id
      DYNAMODB_TABLE_STORES  = aws_dynamodb_table.stores.name
      DYNAMODB_TABLE_UPLOADS = aws_dynamodb_table.uploads.name
      EXTRACTION_LAMBDA_NAME = "${var.project_name}-extraction-worker"
      LOG_LEVEL              = "INFO"
    }
  }

  tags = {
    Name = "Upload Handler"
  }
}

# Extraction Worker Lambda (CSV-only for now)
resource "aws_lambda_function" "extraction_worker" {
  filename         = "../../lambda_packages/extraction_worker_csv_only.zip"
  function_name    = "${var.project_name}-extraction-worker"
  role             = aws_iam_role.extraction_worker.arn
  handler          = "handler.lambda_handler"
  source_code_hash = fileexists("../../lambda_packages/extraction_worker_csv_only.zip") ? filebase64sha256("../../lambda_packages/extraction_worker_csv_only.zip") : ""
  runtime          = "python3.11"
  timeout          = 300 # 5 minutes for LLM calls
  memory_size      = 512 # Reduced for CSV-only

  environment {
    variables = {
      S3_BUCKET_NAME                = aws_s3_bucket.main.id
      DYNAMODB_TABLE_UPLOADS        = aws_dynamodb_table.uploads.name
      DYNAMODB_TABLE_EXTRACTED_DATA = aws_dynamodb_table.extracted_data.name
      GEMINI_API_KEY                = var.gemini_api_key
      OPENAI_API_KEY                = var.openai_api_key
      LLM_PROVIDER                  = "gemini"
      LOG_LEVEL                     = "INFO"
    }
  }

  tags = {
    Name = "Extraction Worker CSV Only"
  }
}

# CloudWatch Log Groups (for better log management)
resource "aws_cloudwatch_log_group" "upload_handler" {
  name              = "/aws/lambda/${aws_lambda_function.upload_handler.function_name}"
  retention_in_days = 7 # Free tier: up to 5GB storage
}

resource "aws_cloudwatch_log_group" "extraction_worker" {
  name              = "/aws/lambda/${aws_lambda_function.extraction_worker.function_name}"
  retention_in_days = 7
}

# Variables for API keys (passed from environment or tfvars)
variable "gemini_api_key" {
  description = "Gemini API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API key (optional)"
  type        = string
  sensitive   = true
  default     = ""
}
