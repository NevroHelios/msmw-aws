"""
DynamoDB client wrapper for common operations.
"""
import os
import boto3
from typing import Dict, List, Optional, Any
from datetime import datetime
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class DynamoDBClient:
    """Wrapper for DynamoDB operations"""
    
    def __init__(self, region: str = None, endpoint_url: str = None):
        """
        Initialize DynamoDB client.
        
        Args:
            region: AWS region (default from env)
            endpoint_url: Optional endpoint for LocalStack
        """
        self.region = region or os.getenv('AWS_REGION', 'ap-south-1')
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=self.region,
            endpoint_url=endpoint_url
        )
        
        # Table names from environment
        self.table_stores = os.getenv('DYNAMODB_TABLE_STORES', 'Stores')
        self.table_uploads = os.getenv('DYNAMODB_TABLE_UPLOADS', 'Uploads')
        self.table_extracted = os.getenv('DYNAMODB_TABLE_EXTRACTED_DATA', 'ExtractedData')
    
    def get_table(self, table_name: str):
        """Get DynamoDB table resource"""
        return self.dynamodb.Table(table_name)
    
    # ========== Store Operations ==========
    
    def get_store(self, store_id: str) -> Optional[Dict]:
        """Get store by ID"""
        try:
            table = self.get_table(self.table_stores)
            response = table.get_item(Key={'store_id': store_id})
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting store {store_id}: {e}")
            return None
    
    def create_store(self, store_data: Dict) -> bool:
        """Create a new store"""
        try:
            table = self.get_table(self.table_stores)
            table.put_item(Item=store_data)
            logger.info(f"Created store: {store_data['store_id']}")
            return True
        except ClientError as e:
            logger.error(f"Error creating store: {e}")
            return False
    
    def list_stores(self) -> List[Dict]:
        """List all stores"""
        try:
            table = self.get_table(self.table_stores)
            response = table.scan()
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error listing stores: {e}")
            return []
    
    # ========== Upload Operations ==========
    
    def create_upload(self, upload_data: Dict) -> bool:
        """Create upload record"""
        try:
            table = self.get_table(self.table_uploads)
            
            # Ensure timestamp is string for DynamoDB
            if isinstance(upload_data.get('uploaded_at'), datetime):
                upload_data['uploaded_at'] = upload_data['uploaded_at'].isoformat()
            
            table.put_item(Item=upload_data)
            logger.info(f"Created upload: {upload_data['upload_id']}")
            return True
        except ClientError as e:
            logger.error(f"Error creating upload: {e}")
            return False
    
    def get_upload(self, store_id: str, upload_id: str) -> Optional[Dict]:
        """Get upload by store_id and upload_id"""
        try:
            table = self.get_table(self.table_uploads)
            response = table.get_item(
                Key={
                    'store_id': store_id,
                    'upload_id': upload_id
                }
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting upload {upload_id}: {e}")
            return None
    
    def update_upload_status(
        self, 
        store_id: str, 
        upload_id: str, 
        status: str,
        error_message: str = None
    ) -> bool:
        """Update upload status"""
        try:
            table = self.get_table(self.table_uploads)
            
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
            return True
        except ClientError as e:
            logger.error(f"Error updating upload status: {e}")
            return False
    
    def list_uploads_by_store(self, store_id: str, limit: int = 50) -> List[Dict]:
        """List uploads for a store"""
        try:
            table = self.get_table(self.table_uploads)
            response = table.query(
                KeyConditionExpression='store_id = :sid',
                ExpressionAttributeValues={':sid': store_id},
                Limit=limit,
                ScanIndexForward=False  # Latest first
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error listing uploads: {e}")
            return []
    
    # ========== Extracted Data Operations ==========
    
    def create_extracted_data(self, extracted_data: Dict) -> bool:
        """Store extracted data"""
        try:
            table = self.get_table(self.table_extracted)
            
            # Ensure timestamp is string
            if isinstance(extracted_data.get('extracted_at'), datetime):
                extracted_data['extracted_at'] = extracted_data['extracted_at'].isoformat()
            
            table.put_item(Item=extracted_data)
            logger.info(f"Stored extracted data: {extracted_data['record_id']}")
            return True
        except ClientError as e:
            logger.error(f"Error storing extracted data: {e}")
            return False
    
    def get_extracted_data(self, store_id: str, record_id: str) -> Optional[Dict]:
        """Get extracted data by record_id"""
        try:
            table = self.get_table(self.table_extracted)
            response = table.get_item(
                Key={
                    'store_id': store_id,
                    'record_id': record_id
                }
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting extracted data: {e}")
            return None
    
    def list_extracted_data_by_store(
        self, 
        store_id: str, 
        data_type: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """List extracted data for a store, optionally filtered by type"""
        try:
            table = self.get_table(self.table_extracted)
            
            if data_type:
                # Use GSI for type filtering
                response = table.query(
                    IndexName='type-date-index',
                    KeyConditionExpression='store_id = :sid AND #type = :dtype',
                    ExpressionAttributeNames={'#type': 'type'},
                    ExpressionAttributeValues={
                        ':sid': store_id,
                        ':dtype': data_type
                    },
                    Limit=limit
                )
            else:
                response = table.query(
                    KeyConditionExpression='store_id = :sid',
                    ExpressionAttributeValues={':sid': store_id},
                    Limit=limit,
                    ScanIndexForward=False
                )
            
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error listing extracted data: {e}")
            return []
    
    # ========== Utility Methods ==========
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            self.get_table(table_name).table_status
            return True
        except ClientError:
            return False
