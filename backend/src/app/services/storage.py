import os
import json
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

_s3_available = None
_cached_client = None

class StorageClient:
    def __init__(self):
        global _s3_available, _cached_client
        self.endpoint = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.local_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage_raw")
        os.makedirs(self.local_dir, exist_ok=True)
        
        if _s3_available is None:
            if settings.MOCK_SERVICES:
                _s3_available = False
                _cached_client = None
                logger.info("MOCK_SERVICES enabled. Storage client falling back to local storage instantly.")
            else:
                # Try to initialize boto3 client with short timeout to fail fast if offline
                from botocore.config import Config
                try:
                    client = boto3.client(
                        "s3",
                        endpoint_url=self.endpoint,
                        aws_access_key_id=self.access_key,
                        aws_secret_access_key=self.secret_key,
                        region_name="us-east-1",
                        config=Config(connect_timeout=1.0, read_timeout=1.0, retries={"max_attempts": 0})
                    )
                    client.list_buckets()
                    _cached_client = client
                    _s3_available = True
                    logger.info("MinIO/S3 storage client connected successfully")
                except Exception as e:
                    logger.warning(f"MinIO/S3 connection failed ({e}). Falling back to local filesystem storage.")
                    _s3_available = False
                    _cached_client = None
                
        self.use_s3 = _s3_available
        self.s3_client = _cached_client

    def upload_raw_payload(self, bucket: str, key: str, payload: Dict[str, Any]) -> str:
        """Uploads raw JSON payload. Returns storage URI string."""
        json_data = json.dumps(payload, indent=2)
        
        if self.use_s3 and self.s3_client:
            try:
                # Ensure bucket exists
                try:
                    self.s3_client.head_bucket(Bucket=bucket)
                except ClientError:
                    self.s3_client.create_bucket(Bucket=bucket)
                    
                self.s3_client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=json_data,
                    ContentType="application/json"
                )
                logger.info(f"Uploaded raw payload to s3://{bucket}/{key}")
                return f"s3://{bucket}/{key}"
            except (BotoCoreError, ClientError) as e:
                logger.error(f"S3 upload failed: {e}. Falling back to local filesystem.")
        
        # Local filesystem fallback
        file_path = os.path.join(self.local_dir, bucket, key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_data)
        safe_path = file_path.replace('\\', '/')
        return f"file:///{safe_path}"

    def get_raw_payload(self, bucket: str, key: str) -> Dict[str, Any]:
        """Retrieves raw JSON payload by bucket and key."""
        if self.use_s3 and self.s3_client:
            try:
                response = self.s3_client.get_object(Bucket=bucket, Key=key)
                return json.loads(response["Body"].read().decode("utf-8"))
            except (BotoCoreError, ClientError) as e:
                logger.error(f"S3 fetch failed: {e}. Checking local filesystem fallback.")
                
        # Local filesystem fallback lookup
        file_path = os.path.join(self.local_dir, bucket, key)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        raise ValueError(f"Payload not found for bucket={bucket}, key={key}")
