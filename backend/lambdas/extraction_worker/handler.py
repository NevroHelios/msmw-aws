"""
Extraction Worker Lambda Function

Processes uploaded files, extracts structured data using pure HTTP APIs,
and stores results in DynamoDB.
"""
import json
import os
import logging
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

# Import extractors (pure HTTP - no heavy SDKs)
from extractors import csv_extractor, image_extractor

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# AWS Clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment configuration
S3_BUCKET = os.getenv('S3_BUCKET_NAME')
TABLE_UPLOADS = os.getenv('DYNAMODB_TABLE_UPLOADS', 'Uploads')
TABLE_EXTRACTED = os.getenv('DYNAMODB_TABLE_EXTRACTED_DATA', 'ExtractedData')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for document extraction.
    
    Expected event format:
    {
        "upload_id": "INV_STORE001_20260215_abc123",
        "store_id": "STORE001",
        "s3_path": "raw/invoices_images/...",
        "file_type": "invoice_image"
    }
    """
    try:
        # Parse event
        upload_id = event['upload_id']
        store_id = event['store_id']
        s3_path = event['s3_path']
        file_type = event['file_type']
        
        logger.info(f"Processing extraction for {upload_id}, type: {file_type}")
        
        # Update status to PROCESSING
        update_upload_status(store_id, upload_id, 'PROCESSING')
        
        # Download file from S3
        logger.info(f"Downloading from s3://{S3_BUCKET}/{s3_path}")
        file_data = download_from_s3(s3_path)
        
        # Extract data based on file type
        extracted_data = extract_data(file_data, file_type, s3_path.split('/')[-1])
        
        # Determine data type for storage
        data_type = get_data_type(file_type)
        
        # Store extracted data in DynamoDB
        extracted_record = {
            'store_id': store_id,
            'record_id': upload_id,
            'type': data_type,
            'data': extracted_data,
            'extraction_method': get_extraction_method(file_type)
        }
        
        store_extracted_data(extracted_record)
        
        # Update upload status to EXTRACTED
        update_upload_status(store_id, upload_id, 'EXTRACTED')
        
        logger.info(f"Successfully extracted {upload_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Extraction successful',
                'upload_id': upload_id
            })
        }
    
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}", exc_info=True)
        
        # Update status to FAILED
        try:
            update_upload_status(store_id, upload_id, 'FAILED', str(e))
        except:
            pass
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def download_from_s3(s3_key: str) -> bytes:
    """Download file from S3"""
    response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
    return response['Body'].read()


def extract_data(file_data: bytes, file_type: str, file_name: str) -> Dict[str, Any]:
    """
    Extract data from file based on type.
    """
    if file_type in ['invoice_image', 'receipt_image']:
        # Use image extractor (pure HTTP to Gemini)
        return image_extractor.extract_from_image(file_data, file_name)
    
    elif file_type in ['sales_csv', 'inventory_csv']:
        # Use CSV extractor (no LLM needed)
        return csv_extractor.extract_from_csv(file_data, file_type)
    
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def get_data_type(file_type: str) -> str:
    """Map file type to data type for storage"""
    type_mapping = {
        'invoice_image': 'invoice',
        'receipt_image': 'receipt',
        'sales_csv': 'sales',
        'inventory_csv': 'inventory'
    }
    return type_mapping.get(file_type, 'unknown')


def get_extraction_method(file_type: str) -> str:
    """Get extraction method for file type"""
    if 'csv' in file_type:
        return 'csv_parse'
    elif 'image' in file_type:
        return 'gemini_vision_api'
    else:
        return 'unknown'


def update_upload_status(store_id: str, upload_id: str, status: str, error_message: str = None):
    """Update upload status in DynamoDB"""
    try:
        table = dynamodb.Table(TABLE_UPLOADS)
        
        update_expr = "SET #status = :status"
        expr_names = {"#status": "status"}
        expr_values = {":status": status}
        
        if error_message:
            update_expr += ", error_message = :error"
            expr_values[":error"] = error_message
        
        table.update_item(
            Key={
                'store_id': store_id,
                'upload_id': upload_id
            },
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
        logger.info(f"Updated upload {upload_id} status to {status}")
    except ClientError as e:
        logger.error(f"Failed to update upload status: {e}")


def store_extracted_data(extracted_data: Dict) -> bool:
    """Store extracted data in DynamoDB"""
    try:
        table = dynamodb.Table(TABLE_EXTRACTED)
        
        # Add timestamp
        from datetime import datetime
        extracted_data['extracted_at'] = datetime.utcnow().isoformat()
        
        table.put_item(Item=extracted_data)
        logger.info(f"Stored extracted data: {extracted_data['record_id']}")
        return True
    except ClientError as e:
        logger.error(f"Failed to store extracted data: {e}")
        return False
