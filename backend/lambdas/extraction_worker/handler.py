"""
Extraction Worker Lambda Function

Processes uploaded files, extracts structured data using LLM/parsers,
and stores results in DynamoDB.
"""
import json
import os
import logging
import tempfile
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

# Import extractors and LLM clients
from extractors.image_extractor import ImageExtractor
from extractors.csv_extractor import CSVExtractor
from extractors.document_extractor import DocumentExtractor
from llm_clients.gemini_client import GeminiClient
from llm_clients.openai_client import OpenAIClient

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
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'gemini')  # gemini or openai


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
        upload_id = event.get('upload_id')
        store_id = event.get('store_id')
        s3_path = event.get('s3_path')
        file_type = event.get('file_type')
        
        if not all([upload_id, store_id, s3_path, file_type]):
            raise ValueError("Missing required event fields")
        
        logger.info(f"Processing extraction for {upload_id}, type: {file_type}")
        
        # Update status to PROCESSING
        update_upload_status(store_id, upload_id, 'PROCESSING')
        
        # Download file from S3
        logger.info(f"Downloading from s3://{S3_BUCKET}/{s3_path}")
        file_data = download_from_s3(s3_path)
        
        if not file_data:
            raise Exception("Failed to download file from S3")
        
        # Initialize LLM client (if needed)
        llm_client = get_llm_client()
        
        # Extract data based on file type
        extracted_data = extract_data(file_data, file_type, s3_path, llm_client)
        
        # Determine data type for storage
        data_type = get_data_type(file_type)
        
        # Store extracted data in DynamoDB
        extracted_record = {
            'store_id': store_id,
            'record_id': upload_id,
            'type': data_type,
            'data': extracted_data,
            'extracted_at': context.request_id,  # Use request ID as timestamp placeholder
            'extraction_method': get_extraction_method(file_type)
        }
        
        if not store_extracted_data(extracted_record):
            raise Exception("Failed to store extracted data")
        
        # Update upload status to EXTRACTED
        update_upload_status(store_id, upload_id, 'EXTRACTED')
        
        logger.info(f"Successfully extracted {upload_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Extraction successful',
                'upload_id': upload_id,
                'extracted_fields': len(extracted_data)
            })
        }
    
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}", exc_info=True)
        
        # Update status to FAILED
        if 'upload_id' in locals() and 'store_id' in locals():
            update_upload_status(
                store_id, 
                upload_id, 
                'FAILED',
                error_message=str(e)
            )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def download_from_s3(s3_key: str) -> bytes:
    """Download file from S3"""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        return response['Body'].read()
    except ClientError as e:
        logger.error(f"S3 download error: {e}")
        return None


def get_llm_client():
    """Get LLM client based on configuration and availability"""
    # Try Gemini first (free tier)
    if GeminiClient.is_available():
        logger.info("Using Gemini LLM client (free tier)")
        return GeminiClient()
    
    # Fallback to OpenAI
    elif OpenAIClient.is_available():
        logger.warning("Using OpenAI LLM client (paid) - Gemini not available")
        return OpenAIClient()
    
    else:
        logger.error("No LLM API keys configured")
        return None


def extract_data(
    file_data: bytes, 
    file_type: str, 
    file_path: str,
    llm_client
) -> Dict[str, Any]:
    """
    Extract data from file based on type.
    
    Args:
        file_data: File bytes
        file_type: Type of file
        file_path: S3 path (for getting extension)
        llm_client: LLM client instance
    
    Returns:
        Extracted data dictionary
    """
    if file_type in ['invoice_image', 'receipt_image', 'purchase_order_image']:
        # Use image extractor
        if not llm_client:
            raise ValueError("LLM client required for image extraction")
        
        mime_type = get_mime_type(file_path)
        extractor = ImageExtractor(llm_client)
        return extractor.extract(file_data, file_type, mime_type)
    
    elif file_type in ['sales_csv', 'inventory_csv']:
        # Use CSV extractor (no LLM needed)
        extractor = CSVExtractor()
        return extractor.extract(file_data, file_type)
    
    elif file_type in ['bank_statement_pdf']:
        # Use document extractor
        if not llm_client:
            raise ValueError("LLM client required for document extraction")
        
        extractor = DocumentExtractor(llm_client)
        return extractor.extract(file_data, file_type, file_path)
    
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def get_mime_type(file_path: str) -> str:
    """Get MIME type from file path"""
    ext = file_path.lower().split('.')[-1]
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'pdf': 'application/pdf'
    }
    return mime_types.get(ext, 'application/octet-stream')


def get_data_type(file_type: str) -> str:
    """Map file type to data type for storage"""
    type_mapping = {
        'invoice_image': 'invoice',
        'purchase_order_image': 'invoice',
        'receipt_image': 'receipt',
        'sales_csv': 'sales',
        'inventory_csv': 'inventory',
        'bank_statement_pdf': 'bank_statement'
    }
    return type_mapping.get(file_type, 'unknown')


def get_extraction_method(file_type: str) -> str:
    """Get extraction method for file type"""
    if 'csv' in file_type:
        return 'csv_parse'
    elif 'image' in file_type:
        return 'llm'
    elif 'pdf' in file_type or 'doc' in file_type:
        return 'llm'
    else:
        return 'unknown'


def update_upload_status(
    store_id: str, 
    upload_id: str, 
    status: str,
    error_message: str = None
):
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
