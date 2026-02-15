# 🚀 Quick Start Guide

Get your MSME Retail Intelligence System up and running in **15 minutes**.

## What You'll Build

A serverless document extraction system that:
- ✅ Uploads invoices, receipts, CSV files
- ✅ Extracts structured data using AI (Gemini - FREE)
- ✅ Stores results in DynamoDB
- ✅ **Costs $0-2/month** (FREE tier compatible)

---

## Prerequisites

- AWS Account ([create free account](https://aws.amazon.com/free/))
- Python 3.11+
- Git

---

## Step-by-Step Setup

### 1️⃣ Get AWS Credentials (5 min)

Follow: **[AWS Setup Guide](docs/AWS_SETUP.md)**

You'll need:
- ✅ AWS Access Key + Secret Key
- ✅ Gemini API Key (free from [Google AI Studio](https://aistudio.google.com/app/apikey))

### 2️⃣ Configure Environment (2 min)

```bash
cd /home/shrek/Desktop/projects/msmw-aws

# Create .env file
cp config/.env.example config/.env

# Edit with your credentials
nano config/.env
# Fill in:
#   AWS_ACCESS_KEY_ID=...
#   AWS_SECRET_ACCESS_KEY=...
#   GEMINI_API_KEY=...
```

### 3️⃣ Verify Setup (1 min)

```bash
# Install dependencies
pip install -r requirements.txt

# Verify everything is configured
python3 scripts/verify_setup.py
```

**Expected**: All checks pass ✅

### 4️⃣ Deploy to AWS (5 min)

```bash
# Package Lambda functions
./scripts/package_lambda.sh

# Deploy infrastructure with Terraform
cd infrastructure/terraform
terraform init
terraform apply -var="gemini_api_key=$GEMINI_API_KEY"
# Type 'yes' to confirm
```

**Wait 2-3 minutes** for deployment to complete.

### 5️⃣ Seed Test Data (1 min)

```bash
cd ../..
python3 scripts/seed_stores.py
```

### 6️⃣ Test It! (1 min)

```bash
# Get your API Gateway URL
cd infrastructure/terraform
terraform output api_gateway_url

# Coming soon: Frontend dashboard to upload files!
```

---

## What Was Created?

| Resource | Purpose | Free Tier |
|----------|---------|-----------|
| **S3 Bucket** | Store raw files (invoices, CSVs) | 5GB free |
| **DynamoDB Tables** | Store structured data | 25GB always free |
| **Lambda Functions** | Process uploads & extract data | 1M requests/month free |
| **API Gateway** | REST API endpoints | 1M calls/month free |
| **IAM Roles** | Secure permissions | Free |

**Total Cost: $0/month** if you stay in free tier! 🎉

---

## Next Steps

### Option A: Use Locally (No AWS Deployment)

Want to test without deploying to AWS first?

Follow: **[Local Development Guide](docs/LOCAL_DEVELOPMENT.md)**

### Option B: Deploy Frontend (Coming Soon)

The Next.js frontend is part of the next phase. For now, you can:
- Test the Lambda functions directly
- Use AWS Console to view data
- Build your own frontend with the API

### Option C: Test the Backend

```bash
# Upload a test file via AWS CLI
aws s3 cp test_invoice.jpg s3://msme-retail-intelligence-<your-account-id>/raw/invoices_images/

# Check extraction results
aws dynamodb scan --table-name ExtractedData
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│              Your System                    │
├─────────────────────────────────────────────┤
│                                             │
│  📤 Upload → 📦 S3 → 🔄 Lambda              │
│                        ↓                    │
│                    🤖 Gemini (FREE)         │
│                        ↓                    │
│                    💾 DynamoDB              │
│                                             │
│  Cost: $0/month ✨                          │
└─────────────────────────────────────────────┘
```

---

## Troubleshooting

### Error: "AWS credentials not found"

```bash
# Configure AWS CLI
aws configure
# Enter your Access Key ID and Secret Access Key
```

### Error: "Gemini API key invalid"

Get a new key: https://aistudio.google.com/app/apikey

### Need Help?

1. Check [Deployment Guide](docs/DEPLOYMENT.md) for detailed troubleshooting
2. Review [AWS Setup Guide](docs/AWS_SETUP.md) for credential issues
3. See [Local Development](docs/LOCAL_DEVELOPMENT.md) for testing without AWS

---

## Project Structure

```
msmw-aws/
├── backend/              # Lambda functions (Python)
│   ├── lambdas/
│   │   ├── upload_handler/       # Handles file uploads
│   │   └── extraction_worker/    # Extracts structured data
│   └── shared/           # Utilities (DynamoDB, S3)
├── infrastructure/       # Terraform (AWS deployment)
│   └── terraform/        # S3, DynamoDB, Lambda configs
├── config/              # Configuration & environment
│   ├── config.yaml       # Global settings
│   └── .env             # Secrets (NOT in git)
├── scripts/             # Helper scripts
│   ├── verify_setup.py   # Check credentials
│   ├── package_lambda.sh # Build Lambda packages
│   └── seed_stores.py    # Create test data
└── docs/                # Documentation
    ├── AWS_SETUP.md      # Get AWS credentials
    ├── DEPLOYMENT.md     # Deploy to AWS
    └── LOCAL_DEVELOPMENT.md
```

---

## Free Tier Limits

As long as you stay under these limits, it's **100% FREE**:

- Lambda: 1M requests/month ✅
- S3: 5GB storage ✅
- DynamoDB: 25GB storage ✅
- Gemini API: 60 requests/minute ✅

**For 500 uploads/month**: $0.00 💰

---

## What's Next?

The backend is **production-ready**! 

Upcoming additions:
1. **Next.js Frontend** - Beautiful UI to upload files and view results
2. **Analytics Dashboard** - Visualize extracted data
3. **Multi-tenant Support** - Multiple businesses on one system
4. **Advanced Features** - OCR, batch processing, webhooks

Stay tuned! 🚀

---

## Clean Up (Delete Everything)

To avoid any charges, destroy all AWS resources:

```bash
cd infrastructure/terraform
terraform destroy -var="gemini_api_key=$GEMINI_API_KEY"
```

This deletes everything (S3, DynamoDB, Lambda). **Use with caution!** ⚠️

---

## Success! 🎉

You now have a **serverless document extraction system** running on AWS Free Tier!

Questions? Check the detailed docs in the `/docs` folder.
