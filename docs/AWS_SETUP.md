# AWS Free Tier Setup Guide

**🎯 Goal**: Get your AWS account ready with **FREE tier only** resources.

This guide will help you:
1. Create an AWS Free Tier account
2. Get your AWS credentials (Access Key & Secret Key)
3. Set up required services (S3, DynamoDB, Lambda)
4. Get LLM API keys (Gemini FREE tier)

---

## ✅ Step 1: Create AWS Free Tier Account

### 1.1 Sign Up for AWS

1. Go to: **https://aws.amazon.com/free/**
2. Click **"Create a Free Account"**
3. Provide:
   - Email address
   - Account name (e.g., "MSME Retail Intelligence")
   - Password
4. Choose **"Personal"** account type
5. Enter contact information
6. **Payment Method**: Credit/debit card required (won't be charged if you stay in free tier)
7. **Identity Verification**: Phone verification
8. Choose **"Basic Support - Free"** plan

> [!IMPORTANT]
> **Free Tier Includes**:
> - Lambda: 1M requests/month (always free)
> - S3: 5GB storage (12 months free)
> - DynamoDB: 25GB storage (always free)
> - API Gateway: 1M calls/month (12 months free)

### 1.2 Sign in to AWS Console

1. Go to: **https://console.aws.amazon.com/**
2. Sign in with your email and password
3. You should see the AWS Management Console dashboard

---

## 🔑 Step 2: Get AWS Credentials

### 2.1 Create IAM User (Recommended for Security)

> [!WARNING]
> **Never use root account credentials!** Create an IAM user instead.

1. **Open IAM Console**:
   - Search for "IAM" in the AWS search bar
   - Click **"IAM"** (Identity and Access Management)

2. **Create User**:
   - Click **"Users"** in the left sidebar
   - Click **"Create user"**
   - Username: `msmw-developer`
   - Click **"Next"**

3. **Set Permissions**:
   - Select **"Attach policies directly"**
   - Search and check these policies:
     - ✅ `AmazonS3FullAccess`
     - ✅ `AmazonDynamoDBFullAccess`
     - ✅ `AWSLambda_FullAccess`
     - ✅ `AmazonAPIGatewayAdministrator`
     - ✅ `IAMFullAccess` (needed to create Lambda execution roles)
     - ✅ `CloudWatchLogsFullAccess`
   - Click **"Next"**
   - Click **"Create user"**

4. **Create Access Key**:
   - Click on the newly created user `msmw-developer`
   - Go to **"Security credentials"** tab
   - Scroll to **"Access keys"** section
   - Click **"Create access key"**
   - Select **"Command Line Interface (CLI)"**
   - Check "I understand..." and click **"Next"**
   - Description (optional): "MSMW Development"
   - Click **"Create access key"**

5. **Download Credentials**:
   - ✅ **Access key ID**: Looks like `AKIAIOSFODNN7EXAMPLE`
   - ✅ **Secret access key**: Looks like `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
   - Click **"Download .csv file"** (SAVE THIS SAFELY!)
   - Click **"Done"**

> [!CAUTION]
> **Keep your Secret Access Key safe!** You can only view it once. If you lose it, you'll need to create a new one.

### 2.2 Get Your AWS Account ID

1. Click on your username in the top-right corner
2. Your **Account ID** is shown (12 digits, e.g., `123456789012`)
3. Copy this - you'll need it for configuration

---

## 🗄️ Step 3: Verify AWS Services Access

### 3.1 Test AWS CLI (Optional but Recommended)

Install AWS CLI to test your credentials:

```bash
# Install AWS CLI (Linux/Mac)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI
aws configure
# Enter:
#   AWS Access Key ID: [paste from CSV]
#   AWS Secret Access Key: [paste from CSV]
#   Default region name: ap-south-1
#   Default output format: json

# Test connection
aws sts get-caller-identity
```

**Expected Output**:
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/msmw-developer"
}
```

### 3.2 Verify Free Tier Services

**Check S3**:
```bash
aws s3 ls
# Should return empty list (no error)
```

**Check DynamoDB**:
```bash
aws dynamodb list-tables
# Should return: {"TableNames": []}
```

**Check Lambda**:
```bash
aws lambda list-functions
# Should return: {"Functions": []}
```

---

## 🤖 Step 4: Get LLM API Keys

### 4.1 Gemini API Key (FREE - Recommended Primary)

> [!TIP]
> **Gemini is FREE** with 15 requests/minute - perfect for free tier!

1. Go to: **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. **Select Project**:
   - Option 1: "Create API key in new project" (recommended)
   - Give it a name: "MSMW Retail Intelligence"
5. Click **"Create API Key"**
6. **Copy the API key**: Looks like `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
7. Save this key securely

**Gemini Free Tier Limits**:
- ✅ 15 requests per minute
- ✅ 1,500 requests per day
- ✅ 1 million tokens per month
- ✅ **Cost: $0/month**

### 4.2 OpenAI API Key (PAID - Optional Fallback)

> [!WARNING]
> **OpenAI is NOT free**. Only set this up if you want a fallback option.

**Costs**:
- GPT-4o-mini: ~$0.00015 per image (cheap)
- GPT-4-vision: ~$0.01-0.03 per image (expensive)

**If you want to use it**:
1. Go to: **https://platform.openai.com/api-keys**
2. Sign in or create an account
3. Click **"Create new secret key"**
4. Name: "MSMW Retail Intelligence"
5. Copy the key: Looks like `sk-proj-XXXXXXXXXXXXXXXXXXXXXXXX`
6. Add payment method in **Billing** section

**Our Recommendation**: **Skip OpenAI** and use Gemini only for free tier.

---

## 🔧 Step 5: Configure Your Project

### 5.1 Create `.env` File

Copy the example and fill in your credentials:

```bash
cd /home/shrek/Desktop/projects/msmw-aws
cp config/.env.example config/.env
nano config/.env  # or use your favorite editor
```

### 5.2 Fill in Your Credentials

Edit `config/.env`:

```bash
# AWS Credentials (from Step 2)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE  # ← Your Access Key
AWS_SECRET_ACCESS_KEY=wJalrXUt...       # ← Your Secret Key
AWS_REGION=ap-south-1                    # ← Mumbai region (free tier)
AWS_ACCOUNT_ID=123456789012              # ← Your Account ID

# LLM API Keys (from Step 4)
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXX      # ← Your Gemini key

# OpenAI (optional - leave blank for free tier)
OPENAI_API_KEY=

# Environment
ENVIRONMENT=development

# These will be auto-filled after deployment
NEXT_PUBLIC_API_GATEWAY_URL=
```

> [!CAUTION]
> **Never commit `.env` to git!** It's already in `.gitignore`.

---

## 🎯 Step 6: Verify Setup

Run the verification script:

```bash
cd /home/shrek/Desktop/projects/msmw-aws
python3 scripts/verify_setup.py
```

**Expected Output**:
```
✅ AWS credentials valid
✅ AWS region: ap-south-1
✅ Account ID: 123456789012
✅ Gemini API key configured
✅ S3 access confirmed
✅ DynamoDB access confirmed
✅ Lambda access confirmed

🎉 Setup complete! You're ready to deploy.
```

---

## 📊 Monitor Free Tier Usage

### Enable Billing Alerts (Recommended)

1. Go to **AWS Billing Dashboard**: https://console.aws.amazon.com/billing/
2. Click **"Billing Preferences"** in the left sidebar
3. Enable:
   - ✅ "Receive Free Tier Usage Alerts"
   - ✅ "Receive Billing Alerts"
4. Enter your email
5. Save preferences

### Set Up Budget Alert

1. Go to **AWS Budgets**: https://console.aws.amazon.com/billing/home#/budgets
2. Click **"Create budget"**
3. Template: **"Zero spend budget"** (recommended)
4. Enter email for alerts
5. Click **"Create budget"**

> [!TIP]
> This will alert you if you accidentally exceed free tier limits!

---

## 🚨 Troubleshooting

### Error: "Access Denied" when running AWS commands

**Solution**: Check IAM permissions
```bash
# Verify your identity
aws sts get-caller-identity

# Check if policies are attached
aws iam list-attached-user-policies --user-name msmw-developer
```

### Error: "Invalid API Key" for Gemini

**Solution**: 
1. Verify the key is correct (no extra spaces)
2. Check if API is enabled: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com
3. Make sure you copied the full key

### Error: "Region not supported"

**Solution**: Use `ap-south-1` (Mumbai) - it's free tier eligible:
```bash
aws configure set region ap-south-1
```

---

## ✅ Checklist

Before proceeding to deployment:

- [ ] AWS account created with free tier
- [ ] IAM user created with proper permissions
- [ ] AWS Access Key and Secret Key downloaded
- [ ] AWS CLI configured and tested
- [ ] Gemini API key obtained
- [ ] `.env` file created with all credentials
- [ ] Billing alerts enabled
- [ ] Verification script passed

---

## 🎓 Next Steps

1. ✅ **You are here**: AWS setup complete
2. ➡️ **Next**: Run `./scripts/deploy_infrastructure.sh` to create AWS resources
3. ➡️ **Then**: Deploy Lambda functions
4. ➡️ **Finally**: Run the Next.js frontend

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

---

## 💡 Free Tier Tips

1. **Always use `ap-south-1` region** - free tier eligible
2. **Set DynamoDB to On-Demand** - no provisioned capacity costs
3. **Use Gemini over OpenAI** - completely free
4. **Delete test resources** - don't leave unused Lambda functions running
5. **Monitor usage monthly** - check AWS Cost Explorer

**With proper setup, your monthly cost should be $0-2!** 🎉
