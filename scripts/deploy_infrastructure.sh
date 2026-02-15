#!/bin/bash
# Deploy infrastructure using AWS CLI (no Terraform needed)

set -e

echo "🚀 Deploying AWS Infrastructure..."

# Load environment variables
source config/.env

# Create S3 bucket
echo "📦 Creating S3 bucket..."
aws s3 mb s3://msme-retail-intelligence-${AWS_ACCOUNT_ID} --region ${AWS_REGION} || echo "Bucket already exists"

# Enable versioning (optional)
aws s3api put-bucket-versioning \
  --bucket msme-retail-intelligence-${AWS_ACCOUNT_ID} \
  --versioning-configuration Status=Disabled

# Create DynamoDB tables
echo "💾 Creating DynamoDB tables..."

# Table 1: Stores
aws dynamodb create-table \
  --table-name Stores \
  --attribute-definitions AttributeName=store_id,AttributeType=S \
  --key-schema AttributeName=store_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ${AWS_REGION} || echo "Stores table already exists"

# Table 2: Uploads
aws dynamodb create-table \
  --table-name Uploads \
  --attribute-definitions \
    AttributeName=store_id,AttributeType=S \
    AttributeName=upload_id,AttributeType=S \
    AttributeName=status,AttributeType=S \
  --key-schema \
    AttributeName=store_id,KeyType=HASH \
    AttributeName=upload_id,KeyType=RANGE \
  --global-secondary-indexes \
    "[
      {
        \"IndexName\": \"status-index\",
        \"KeySchema\": [{\"AttributeName\":\"status\",\"KeyType\":\"HASH\"}],
        \"Projection\":{\"ProjectionType\":\"ALL\"}
      }
    ]" \
  --billing-mode PAY_PER_REQUEST \
  --region ${AWS_REGION} || echo "Uploads table already exists"

# Table 3: ExtractedData
aws dynamodb create-table \
  --table-name ExtractedData \
  --attribute-definitions \
    AttributeName=store_id,AttributeType=S \
    AttributeName=record_id,AttributeType=S \
    AttributeName=type,AttributeType=S \
  --key-schema \
    AttributeName=store_id,KeyType=HASH \
    AttributeName=record_id,KeyType=RANGE \
  --global-secondary-indexes \
    "[
      {
        \"IndexName\": \"type-index\",
        \"KeySchema\": [
          {\"AttributeName\":\"store_id\",\"KeyType\":\"HASH\"},
          {\"AttributeName\":\"type\",\"KeyType\":\"RANGE\"}
        ],
        \"Projection\":{\"ProjectionType\":\"ALL\"}
      }
    ]" \
  --billing-mode PAY_PER_REQUEST \
  --region ${AWS_REGION} || echo "ExtractedData table already exists"

echo "⏳ Waiting for tables to become active..."
aws dynamodb wait table-exists --table-name Stores --region ${AWS_REGION}
aws dynamodb wait table-exists --table-name Uploads --region ${AWS_REGION}
aws dynamodb wait table-exists --table-name ExtractedData --region ${AWS_REGION}

# Create IAM role for upload handler
echo "🔐 Creating IAM roles..."
cat > /tmp/upload-handler-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name msme-upload-handler-role \
  --assume-role-policy-document file:///tmp/upload-handler-trust-policy.json || echo "Upload handler role exists"

# Create IAM role for extraction worker
aws iam create-role \
  --role-name msme-extraction-worker-role \
  --assume-role-policy-document file:///tmp/upload-handler-trust-policy.json || echo "Extraction worker role exists"

# Attach basic Lambda execution policy
aws iam attach-role-policy \
  --role-name msme-upload-handler-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole || true

aws iam attach-role-policy \
  --role-name msme-extraction-worker-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole || true

# Create inline policy for upload handler
cat > /tmp/upload-handler-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": "arn:aws:s3:::msme-retail-intelligence-${AWS_ACCOUNT_ID}/*"
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"],
      "Resource": [
        "arn:aws:dynamodb:${AWS_REGION}:${AWS_ACCOUNT_ID}:table/Stores",
        "arn:aws:dynamodb:${AWS_REGION}:${AWS_ACCOUNT_ID}:table/Uploads"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["lambda:InvokeFunction"],
      "Resource": "arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:msme-extraction-worker"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name msme-upload-handler-role \
  --policy-name upload-handler-policy \
  --policy-document file:///tmp/upload-handler-policy.json

# Create inline policy for extraction worker
cat > /tmp/extraction-worker-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::msme-retail-intelligence-${AWS_ACCOUNT_ID}/*"
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query"],
      "Resource": [
        "arn:aws:dynamodb:${AWS_REGION}:${AWS_ACCOUNT_ID}:table/Uploads",
        "arn:aws:dynamodb:${AWS_REGION}:${AWS_ACCOUNT_ID}:table/ExtractedData"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name msme-extraction-worker-role \
  --policy-name extraction-worker-policy \
  --policy-document file:///tmp/extraction-worker-policy.json

echo "⏳ Waiting for IAM roles to propagate..."
sleep 10

# Deploy Lambda functions
echo "🚀 Deploying Lambda functions..."

# Upload handler
aws lambda create-function \
  --function-name msme-upload-handler \
  --runtime python3.11 \
  --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/msme-upload-handler-role \
  --handler handler.lambda_handler \
  --zip-file fileb://lambda_packages/upload_handler.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment "Variables={
    S3_BUCKET_NAME=msme-retail-intelligence-${AWS_ACCOUNT_ID},
    DYNAMODB_TABLE_STORES=Stores,
    DYNAMODB_TABLE_UPLOADS=Uploads,
    EXTRACTION_LAMBDA_NAME=msme-extraction-worker,
    LOG_LEVEL=INFO
  }" \
  --region ${AWS_REGION} || \
  aws lambda update-function-code \
    --function-name msme-upload-handler \
    --zip-file fileb://lambda_packages/upload_handler.zip \
    --region ${AWS_REGION}

# Extraction worker
aws lambda create-function \
  --function-name msme-extraction-worker \
  --runtime python3.11 \
  --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/msme-extraction-worker-role \
  --handler handler.lambda_handler \
  --zip-file fileb://lambda_packages/extraction_worker.zip \
  --timeout 300 \
  --memory-size 1024 \
  --environment "Variables={
    S3_BUCKET_NAME=msme-retail-intelligence-${AWS_ACCOUNT_ID},
    DYNAMODB_TABLE_UPLOADS=Uploads,
    DYNAMODB_TABLE_EXTRACTED_DATA=ExtractedData,
    GEMINI_API_KEY=,
    OPENAI_API_KEY=,
    LLM_PROVIDER=gemini,
    LOG_LEVEL=INFO
  }" \
  --region ${AWS_REGION} || \
  aws lambda update-function-code \
    --function-name msme-extraction-worker \
    --zip-file fileb://lambda_packages/extraction_worker.zip \
    --region ${AWS_REGION}

echo "✅ Infrastructure deployed successfully!"
echo ""
echo "📊 Resources created:"
echo "  - S3 Bucket: msme-retail-intelligence-${AWS_ACCOUNT_ID}"
echo "  - DynamoDB Tables: Stores, Uploads, ExtractedData"
echo "  - Lambda: msme-upload-handler"
echo "  - Lambda: msme-extraction-worker"
echo ""
echo "🎯 Next steps:"
echo "  1. Seed test data: python3 scripts/seed_stores.py"
echo "  2. Test upload: Use the Next.js frontend"
