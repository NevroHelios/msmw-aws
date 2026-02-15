# Deployment Guide

Complete guide to deploy the MSME Retail Intelligence System to AWS.

## Prerequisites

Before deploying, ensure you have completed:
- ✅ [AWS Setup Guide](AWS_SETUP.md) - AWS account and credentials configured
- ✅ Gemini API key obtained (free tier)
- ✅ `.env` file created in `config/` directory

## Quick Start (5 Steps)

### Step 1: Verify Setup

```bash
cd /home/shrek/Desktop/projects/msmw-aws

# Install Python dependencies for verification
pip install boto3 python-dotenv

# Run verification
python3 scripts/verify_setup.py
```

**Expected output**: All checks should pass ✅

### Step 2: Install Terraform

```bash
# Install Terraform (if not already installed)
wget https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
unzip terraform_1.7.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform --version
```

### Step 3: Package Lambda Functions

```bash
# Install Lambda dependencies and create deployment packages
./scripts/package_lambda.sh
```

This creates `lambda_packages/upload_handler.zip` and `lambda_packages/extraction_worker.zip`.

### Step 4: Deploy Infrastructure with Terraform

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review what will be created
terraform plan \
  -var="gemini_api_key=$GEMINI_API_KEY" \
  -var="openai_api_key=$OPENAI_API_KEY"

# Deploy (confirm with 'yes')
terraform apply \
  -var="gemini_api_key=$GEMINI_API_KEY" \
  -var="openai_api_key=$OPENAI_API_KEY"
```

**This creates**:
- ✅ S3 bucket for file storage
- ✅ 3 DynamoDB tables (Stores, Uploads, ExtractedData)
- ✅ 2 Lambda functions (upload-handler, extraction-worker)
- ✅ IAM roles with proper permissions
- ✅ CloudWatch log groups

**Deployment time**: ~2-3 minutes

### Step 5: Get API Gateway URL

```bash
# After deployment completes, get the API Gateway URL
terraform output api_gateway_url

# Copy this URL - you'll need it for the frontend
```

Save the URL to `config/.env`:
```bash
NEXT_PUBLIC_API_GATEWAY_URL=<your-api-gateway-url>
```

## Seed Initial Data

Create a test store in DynamoDB:

```bash
cd /home/shrek/Desktop/projects/msmw-aws

python3 scripts/seed_stores.py
```

## Test the Deployment

### Test 1: Upload Handler

```bash
# Test upload endpoint
curl -X POST <api-gateway-url>/upload \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "STORE001",
    "file_type": "sales_csv",
    "file_name": "test.csv",
    "file_content": "base64_encoded_content_here"
  }'
```

### Test 2: Check DynamoDB

```bash
# List uploads
aws dynamodb scan --table-name Uploads --max-items 5

# List extracted data
aws dynamodb scan --table-name ExtractedData --max-items 5
```

### Test 3: Check CloudWatch Logs

```bash
# Upload handler logs
aws logs tail /aws/lambda/msme-retail-intelligence-upload-handler --follow

# Extraction worker logs
aws logs tail /aws/lambda/msme-retail-intelligence-extraction-worker --follow
```

## Deployment Architecture

```
┌─────────────────┐
│   Next.js App   │ (Frontend - to be deployed)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  API Gateway    │ (REST API)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Upload Lambda   │ → S3 (raw files)
└────────┬────────┘       ↓
         │            ┌──────────────┐
         ↓            │   Extraction  │
    Trigger          │    Lambda     │
                     └───────┬───────┘
                             │
                      ┌──────┴──────┐
                      ↓             ↓
                  Gemini API   DynamoDB
                  (FREE)       (ExtractedData)
```

## Cost Monitoring

### View Current Usage

```bash
# Check S3 usage
aws s3 ls s3://msme-retail-intelligence-<account-id> --recursive --summarize

# Check DynamoDB metrics
aws dynamodb describe-table --table-name Uploads | grep TableSizeBytes

# Check Lambda invocations (last 7 days)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=msme-retail-intelligence-upload-handler \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum
```

### Set Up Billing Alerts

1. Go to [AWS Billing Console](https://console.aws.amazon.com/billing/)
2. Create a budget with **$5 threshold**
3. Enable email alerts

## Update Lambda Functions (After Code Changes)

```bash
# Re-package Lambdas
./scripts/package_lambda.sh

# Re-deploy with Terraform
cd infrastructure/terraform
terraform apply \
  -var="gemini_api_key=$GEMINI_API_KEY"
```

## Destroy Infrastructure (Clean Up)

**To avoid charges, destroy resources when not in use:**

```bash
cd infrastructure/terraform

# Review what will be destroyed
terraform plan -destroy

# Destroy all resources
terraform destroy \
  -var="gemini_api_key=$GEMINI_API_KEY"
```

> [!CAUTION]
> This will **permanently delete** all data in S3 and DynamoDB!

## Troubleshooting

### Error: "AccessDenied" during deployment

**Solution**: Check IAM permissions:
```bash
aws iam get-user
aws iam list-attached-user-policies --user-name msmw-developer
```

Ensure you have these policies:
- AmazonS3FullAccess
- AmazonDynamoDBFullAccess
- AWSLambda_FullAccess
- AmazonAPIGatewayAdministrator

### Error: "Lambda package too large"

**Solution**: The extraction worker with dependencies might be >50MB.

Use Lambda Layers:
```bash
# Create layer for dependencies
cd backend/lambdas/extraction_worker
mkdir python
pip install -r requirements.txt -t python/
zip -r layer.zip python/
aws lambda publish-layer-version \
  --layer-name msme-dependencies \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```

Then update `lambda.tf` to use the layer.

### Error: "Gemini API rate limit"

Gemini free tier limits:
- 15 requests/minute
- 1,500 requests/day

**Solution**: Add rate limiting or switch to OpenAI as fallback.

### Lambda timeout errors

**Solution**: Increase timeout in `lambda.tf`:
```hcl
resource "aws_lambda_function" "extraction_worker" {
  timeout = 600  # 10 minutes (max for free tier)
}
```

## Next Steps

1. ✅ **Infrastructure deployed**: You're here
2. ➡️ **Deploy Frontend**: See Frontend deployment guide
3. ➡️ **Test End-to-End**: Upload a test invoice image
4. ➡️ **Production Setup**: Use different AWS account for prod

## Free Tier Limits Summary

| Service      | Free Tier Limit               | Your Usage (est.) | Status |
|-------------|-------------------------------|-------------------|--------|
| Lambda      | 1M requests/month             | ~1,000/month      | ✅ Safe |
| S3          | 5GB storage                   | ~100MB/month      | ✅ Safe |
| DynamoDB    | 25GB storage                  | ~50MB/month       | ✅ Safe |
| API Gateway | 1M calls/month                | ~1,000/month      | ✅ Safe |
| CloudWatch  | 5GB logs                      | ~100MB/month      | ✅ Safe |
| **Gemini**  | **60 req/min FREE**           | **~500/month**    | **✅ FREE** |

**Estimated cost: $0-2/month** (only if you exceed free tier)

---

## Security Best Practices

### Production Deployment

For production:

1. **Use AWS Secrets Manager** for API keys (instead of env vars)
2. **Enable API Gateway authentication** (API keys or Cognito)
3. **Set up VPC** for Lambda functions
4. **Enable S3 bucket encryption** with KMS
5. **Use separate AWS account** for prod
6. **Enable CloudTrail** for audit logging
7. **Set up backup** for DynamoDB (Point-in-Time Recovery)

### Environment Separation

```bash
# Use Terraform workspaces
terraform workspace new production
terraform workspace select production
terraform apply -var="environment=production"
```

---

That's it! Your system is now deployed and ready to process documents. 🎉
