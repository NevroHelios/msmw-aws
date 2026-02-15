# DynamoDB Tables
# FREE TIER: 25GB storage (always free) + 25 WCU/RCU

# Table 1: Stores
resource "aws_dynamodb_table" "stores" {
  name           = "Stores"
  billing_mode   = "PAY_PER_REQUEST"  # Free tier friendly, scales automatically
  hash_key       = "store_id"
  
  attribute {
    name = "store_id"
    type = "S"
  }
  
  tags = {
    Name = "Stores"
  }
}

# Table 2: Uploads
resource "aws_dynamodb_table" "uploads" {
  name           = "Uploads"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "store_id"
  range_key      = "upload_id"
  
  attribute {
    name = "store_id"
    type = "S"
  }
  
  attribute {
    name = "upload_id"
    type = "S"
  }
  
  attribute {
    name = "status"
    type = "S"
  }
  
  # GSI for querying by status
  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    projection_type = "ALL"
  }
  
  tags = {
    Name = "Uploads"
  }
}

# Table 3: Extracted Data
resource "aws_dynamodb_table" "extracted_data" {
  name           = "ExtractedData"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "store_id"
  range_key      = "record_id"
  
  attribute {
    name = "store_id"
    type = "S"
  }
  
  attribute {
    name = "record_id"
    type = "S"
  }
  
  attribute {
    name = "type"
    type = "S"
  }
  
  # GSI for querying by type
  global_secondary_index {
    name            = "type-index"
    hash_key        = "store_id"
    range_key       = "type"
    projection_type = "ALL"
  }
  
  tags = {
    Name = "ExtractedData"
  }
}

# Table 4: Analysis Results (The output of Risk/Demand Lambdas)
resource "aws_dynamodb_table" "analysis_results" {
  name           = "AnalysisResults"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "store_id"
  range_key      = "analysis_id" # unique ID for each report run

  attribute {
    name = "store_id"
    type = "S"
  }

  attribute {
    name = "analysis_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  # GSI to get latest reports for a store
  global_secondary_index {
    name            = "timestamp-index"
    hash_key        = "store_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  tags = {
    Name = "AnalysisResults"
  }
}
