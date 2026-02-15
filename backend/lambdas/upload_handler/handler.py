"""
Upload Handler Lambda Function

Receives file uploads, stores to S3, creates DynamoDB record,
and triggers extraction Lambda asynchronously.
"""
import json
import os
import base64
import uuid
import logging
from datetime import datetime
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# AWS Clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Configuration from environment
S3_BUCKET = os.getenv('S3_BUCKET_NAME')
TABLE_STORES = os.getenv('DYNAMODB_TABLE_STORES', 'Stores')
TABLE_UPLOADS = os.getenv('DYNAMODB_TABLE_UPLOADS', 'Uploads')
EXTRACTION_LAMBDA = os.getenv('EXTRACTION_LAMBDA_NAME', 'extraction-worker')

# File type to S3 folder mapping
FILE_TYPE_FOLDERS = {
    'invoice_image': 'raw/invoices_images/',
    'receipt_image': 'raw/receipts_images/',
    'sales_csv': 'raw/sales_csv/',
    'inventory_csv': 'raw/sales_csv/',
    'bank_statement_pdf': 'raw/documents/',
    'purchase_order_image': 'raw/invoices_images/'
}

# Max file sizes (MB)
MAX_FILE_SIZE_MB = 10


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for file uploads.
    
    Expected event format:
    {
        "body": {
            "store_id": "STORE001",
            "file_type": "invoice_image",
            "file_name": "invoice.jpg",
            "file_content": "base64_encoded_file_content"
        }
    }
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Validate required fields
        store_id = body.get('store_id')
        file_type = body.get('file_type')
        file_name = body.get('file_name')
        file_content = body.get('file_content')  # Base64 encoded
        
        if not all([store_id, file_type, file_name, file_content]):
            return error_response(
                400, 
                "Missing required fields: store_id, file_type, file_name, file_content"
            )
        
        # Validate file type
        if file_type not in FILE_TYPE_FOLDERS:
            return error_response(
                400,
                f"Invalid file_type. Allowed: {list(FILE_TYPE_FOLDERS.keys())}"
            )
        
        # Validate store exists
        if not validate_store(store_id):
            return error_response(404, f"Store {store_id} not found")
        
        # Decode file content
        try:
            file_bytes = base64.b64decode(file_content)
        except Exception as e:
            return error_response(400, f"Invalid base64 file content: {str(e)}")
        
        # Check file size
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return error_response(
                400,
                f"File too large: {file_size_mb:.2f}MB (max {MAX_FILE_SIZE_MB}MB)"
            )
        
        # Generate upload ID and S3 key
        upload_id = generate_upload_id(store_id, file_type)
        s3_key = generate_s3_key(store_id, file_type, file_name)
        
        # Upload to S3
        if not upload_to_s3(file_bytes, s3_key, file_name):
            return error_response(500, "Failed to upload file to S3")
        
        # Create upload record in DynamoDB
        upload_record = {
            'store_id': store_id,
            'upload_id': upload_id,
            'file_type': file_type,
            's3_path': s3_key,
            'status': 'UPLOADED',
            'uploaded_at': datetime.utcnow().isoformat(),
            'file_name': file_name,
            'file_size_mb': round(file_size_mb, 2)
        }
        
        if not create_upload_record(upload_record):
            return error_response(500, "Failed to create upload record")
        
        # Trigger extraction Lambda asynchronously
        trigger_extraction(upload_id, store_id, s3_key, file_type)
        
        logger.info(f"Upload successful: {upload_id}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'message': 'Upload successful',
                'upload_id': upload_id,
                's3_path': s3_key,
                'status': 'UPLOADED'
            })
        }
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, f"Internal server error: {str(e)}")


def validate_store(store_id: str) -> bool:
    """Check if store exists in DynamoDB"""
    try:
        table = dynamodb.Table(TABLE_STORES)
        response = table.get_item(Key={'store_id': store_id})
        return 'Item' in response
    except ClientError as e:
        logger.error(f"Error validating store: {e}")
        return False


def generate_upload_id(store_id: str, file_type: str) -> str:
    """Generate unique upload ID"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    prefix = file_type.split('_')[0].upper()[:3]  # INV, REC, SAL, etc.
    return f"{prefix}_{store_id}_{timestamp}_{unique_id}"


def generate_s3_key(store_id: str, file_type: str, file_name: str) -> str:
    """Generate S3 key (path) for the file"""
    folder = FILE_TYPE_FOLDERS[file_type]
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    # Sanitize filename
    safe_name = file_name.replace(' ', '_').replace('/', '_')
    return f"{folder}{store_id}_{timestamp}_{safe_name}"


def upload_to_s3(file_bytes: bytes, s3_key: str, file_name: str) -> bool:
    """Upload file to S3"""
    try:
        # Determine content type from filename
        content_type = get_content_type(file_name)
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type
        )
        logger.info(f"Uploaded to S3: s3://{S3_BUCKET}/{s3_key}")
        return True
    except ClientError as e:
        logger.error(f"S3 upload error: {e}")
        return False


def get_content_type(file_name: str) -> str:
    """Get MIME type from filename"""
    ext = file_name.lower().split('.')[-1]
    content_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'pdf': 'application/pdf',
        'csv': 'text/csv',
        'txt': 'text/plain'
    }
    return content_types.get(ext, 'application/octet-stream')


def create_upload_record(upload_data: Dict) -> bool:
    """Create upload record in DynamoDB"""
    try:
        table = dynamodb.Table(TABLE_UPLOADS)
        table.put_item(Item=upload_data)
        logger.info(f"Created upload record: {upload_data['upload_id']}")
        return True
    except ClientError as e:
        logger.error(f"DynamoDB put error: {e}")
        return False


def trigger_extraction(upload_id: str, store_id: str, s3_path: str, file_type: str):
    """Trigger extraction Lambda asynchronously"""
    try:
        payload = {
            'upload_id': upload_id,
            'store_id': store_id,
            's3_path': s3_path,
            'file_type': file_type
        }
        
        lambda_client.invoke(
            FunctionName=EXTRACTION_LAMBDA,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )
        logger.info(f"Triggered extraction for {upload_id}")
    except ClientError as e:
        logger.error(f"Failed to trigger extraction Lambda: {e}")
        # Don't fail the upload if extraction trigger fails


def error_response(status_code: int, message: str) -> Dict:
    """Generate error response"""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps({
            'error': message
        })
    }


def get_cors_headers() -> Dict:
    """CORS headers for API Gateway"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Store-Id,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }


# Health check endpoint
def health_check(event: Dict, context: Any) -> Dict:
    """Health check endpoint"""
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps({'status': 'healthy'})
    }
