#!/usr/bin/env python3
"""
Verification script to check AWS setup and credentials
"""
import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def print_status(message, success=True):
    """Print status message with color"""
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = "config/.env"
    
    if not os.path.exists(env_path):
        print_status(f"{env_path} not found", False)
        print("   Create it from config/.env.example")
        return False
    
    print_status(f"{env_path} exists")
    return True

def check_aws_credentials():
    """Verify AWS credentials"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        print_status("AWS credentials valid")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")
        return True
    except NoCredentialsError:
        print_status("AWS credentials not configured", False)
        print("   Run: aws configure")
        return False
    except ClientError as e:
        print_status(f"AWS credentials error: {e}", False)
        return False

def check_aws_region():
    """Check AWS region"""
    try:
        session = boto3.session.Session()
        region = session.region_name or os.getenv('AWS_REGION')
        
        if region:
            print_status(f"AWS region: {region}")
            if region != 'ap-south-1':
                print("   ⚠️  Recommended region for free tier: ap-south-1")
            return True
        else:
            print_status("AWS region not set", False)
            return False
    except Exception as e:
        print_status(f"Region check error: {e}", False)
        return False

def check_gemini_api():
    """Check if Gemini API key is set"""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if api_key and len(api_key) > 10:
        print_status("Gemini API key configured")
        return True
    else:
        print_status("Gemini API key not found", False)
        print("   Get it from: https://aistudio.google.com/app/apikey")
        return False

def check_openai_api():
    """Check if OpenAI API key is set (optional)"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key and len(api_key) > 10:
        print_status("OpenAI API key configured (optional)")
    else:
        print("ℹ️  OpenAI API key not set (optional fallback)")

def check_aws_services():
    """Test access to AWS services"""
    try:
        # Test S3
        s3 = boto3.client('s3')
        s3.list_buckets()
        print_status("S3 access confirmed")
    except ClientError as e:
        print_status(f"S3 access error: {e}", False)
        return False
    
    try:
        # Test DynamoDB
        dynamodb = boto3.client('dynamodb')
        dynamodb.list_tables()
        print_status("DynamoDB access confirmed")
    except ClientError as e:
        print_status(f"DynamoDB access error: {e}", False)
        return False
    
    try:
        # Test Lambda
        lambda_client = boto3.client('lambda')
        lambda_client.list_functions(MaxItems=1)
        print_status("Lambda access confirmed")
    except ClientError as e:
        print_status(f"Lambda access error: {e}", False)
        return False
    
    return True

def main():
    """Run all verification checks"""
    print("\n🔍 Verifying MSME Retail Intelligence Setup...\n")
    
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv('config/.env')
    
    results = []
    
    # Run checks
    results.append(check_env_file())
    results.append(check_aws_credentials())
    results.append(check_aws_region())
    results.append(check_gemini_api())
    check_openai_api()  # Optional
    results.append(check_aws_services())
    
    # Final verdict
    print("\n" + "="*50)
    if all(results):
        print("🎉 Setup complete! You're ready to deploy.")
        print("\nNext steps:")
        print("1. cd infrastructure/terraform")
        print("2. terraform init")
        print("3. terraform plan")
        print("4. terraform apply")
        sys.exit(0)
    else:
        print("⚠️  Setup incomplete. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
