"""
S3 client wrapper for file operations.
"""
import os
import boto3
from typing import Optional
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class S3Client:
    """Wrapper for S3 operations"""
    
    def __init__(self, bucket_name: str = None, region: str = None, endpoint_url: str = None):
        """
        Initialize S3 client.
        
        Args:
            bucket_name: S3 bucket name (default from env)
            region: AWS region (default from env)
            endpoint_url: Optional endpoint for LocalStack
        """
        self.region = region or os.getenv('AWS_REGION', 'ap-south-1')
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET_NAME')
        
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME must be set in environment or passed to constructor")
        
        self.s3_client = boto3.client(
            's3',
            region_name=self.region,
            endpoint_url=endpoint_url
        )
        self.s3_resource = boto3.resource(
            's3',
            region_name=self.region,
            endpoint_url=endpoint_url
        )
    
    def upload_file(
        self, 
        file_path: str, 
        s3_key: str,
        content_type: str = None
    ) -> bool:
        """
        Upload a file to S3.
        
        Args:
            file_path: Local file path
            s3_key: S3 object key (path in bucket)
            content_type: MIME type (optional)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args if extra_args else None
            )
            logger.info(f"Uploaded {file_path} to s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            return False
    
    def upload_fileobj(
        self, 
        file_obj, 
        s3_key: str,
        content_type: str = None
    ) -> bool:
        """
        Upload a file object to S3.
        
        Args:
            file_obj: File-like object
            s3_key: S3 object key
            content_type: MIME type (optional)
        
        Returns:
            True if successful
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args if extra_args else None
            )
            logger.info(f"Uploaded file object to s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file object to S3: {e}")
            return False
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3.
        
        Args:
            s3_key: S3 object key
            local_path: Local file path to save to
        
        Returns:
            True if successful
        """
        try:
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )
            logger.info(f"Downloaded s3://{self.bucket_name}/{s3_key} to {local_path}")
            return True
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {e}")
            return False
    
    def get_object(self, s3_key: str) -> Optional[bytes]:
        """
        Get object content as bytes.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            File content as bytes, or None if error
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Error getting object from S3: {e}")
            return None
    
    def object_exists(self, s3_key: str) -> bool:
        """
        Check if an object exists in S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError:
            return False
    
    def delete_object(self, s3_key: str) -> bool:
        """
        Delete an object from S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Deleted s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting object from S3: {e}")
            return False
    
    def generate_presigned_url(
        self, 
        s3_key: str, 
        expiration: int = 3600,
        http_method: str = 'get_object'
    ) -> Optional[str]:
        """
        Generate a presigned URL for S3 object access.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)
            http_method: HTTP method ('get_object' or 'put_object')
        
        Returns:
            Presigned URL string, or None if error
        """
        try:
            url = self.s3_client.generate_presigned_url(
                http_method,
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
    
    def list_objects(self, prefix: str = '', max_keys: int = 1000) -> list:
        """
        List objects in bucket with given prefix.
        
        Args:
            prefix: Key prefix to filter by
            max_keys: Maximum number of keys to return
        
        Returns:
            List of object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            if 'Contents' not in response:
                return []
            
            return [obj['Key'] for obj in response['Contents']]
        except ClientError as e:
            logger.error(f"Error listing objects: {e}")
            return []
