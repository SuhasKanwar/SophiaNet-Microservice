import sys
import boto3
import uuid
from utils.logger import logger
from utils.exception import SophiaNetException

class S3Syncer():
    def __init__(self, bucket_name: str, object_key: str):
        self.bucket_name = bucket_name
        self.object_key = object_key
        self.s3_client = boto3.client('s3')
    
    def upload_file(self, data: bytes) -> str:
        try:
            file_name = f"{uuid.uuid4()}.png"

            self.s3_client.upload_file(file_name, self.bucket_name, self.object_key, ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/png'})

            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{self.object_key}{file_name}"
            logger.info(f"File uploaded to S3: {s3_url}")
            return s3_url
        except Exception as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise SophiaNetException(f"S3 upload error: {str(e)}", sys)