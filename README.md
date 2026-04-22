# MSME Retail Intelligence System

AWS-based document extraction system for retail intelligence analytics. Processes invoices, receipts, CSV files, and documents using LLM extraction and stores structured data.

## 🚀 Quick Start

### Prerequisites
- AWS Account (Free Tier)
- Python 3.11+
- Node.js 18+
- Terraform 1.5+ (optional, for infrastructure deployment)

### Setup Guides
1. **[AWS Setup Guide](docs/AWS_SETUP.md)** - Get your AWS credentials and API keys
2. **[Local Development](docs/LOCAL_DEVELOPMENT.md)** - Run locally without AWS
3. **[Deployment Guide](docs/DEPLOYMENT.md)** - Deploy to AWS

## 🏗 Architecture

```
Client (Next.js) → API Gateway → Upload Lambda → S3 (raw files)
                                      ↓
                                  Extraction Lambda → Gemini/OpenAI → DynamoDB
```

### Components
- **Backend**: Python 3.11 Lambda functions
- **Frontend**: Next.js 14 with TypeScript
- **Storage**: AWS S3 (raw files) + DynamoDB (structured data)
- **LLM**: Gemini (primary, free tier) + OpenAI (fallback)

## 📁 Project Structure

```
msmw-aws/
├── backend/               # Lambda functions
│   ├── lambdas/
│   │   ├── upload_handler/
│   │   └── extraction_worker/
│   └── shared/           # Shared utilities
├── frontend/             # Next.js app
├── infrastructure/       # Terraform configs
├── config/              # Configuration files
├── scripts/             # Deployment scripts
└── docs/                # Documentation
```

## 💰 Cost Estimate

**Free Tier (First 12 months + Always Free)**:
- Lambda: **FREE** (1M requests/month always free)
- S3: **FREE** (5GB storage for 12 months)
- DynamoDB: **FREE** (25GB always free)
- API Gateway: **FREE** (1M calls/month for 12 months)
- Gemini API: **FREE** (60 requests/minute)

**Estimated Monthly Cost: $0-5** (only if you exceed free tier limits)

## 🛠 Development

### Local Development (No AWS Required)
```bash
# Run backend locally with LocalStack
./scripts/run_local.sh

# Run frontend
cd frontend
npm install
npm run dev
```

### Deploy to AWS
```bash
# Deploy infrastructure
cd infrastructure/terraform
terraform init
terraform apply

# Deploy Lambda functions
./scripts/deploy_lambda.sh
```

## 📚 Documentation

- [AWS Setup Guide](docs/AWS_SETUP.md) - Complete AWS account setup
- [Local Development](docs/LOCAL_DEVELOPMENT.md) - Run without AWS
- [API Documentation](docs/API.md) - API endpoints and usage
- [Configuration Guide](docs/CONFIGURATION.md) - Environment variables and config

## 🔒 Security

- Never commit `.env` files
- Use IAM roles for Lambda (not hardcoded keys)
- API keys stored in AWS Secrets Manager (production)
