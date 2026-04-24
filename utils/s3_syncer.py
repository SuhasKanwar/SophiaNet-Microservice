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
    
    def upload_file(self, data: bytes, content_type: str = "image/png", acl: str = "public-read") -> str:
        try:
            if not isinstance(data, (bytes, bytearray)):
                raise ValueError("data must be bytes")

            key_candidate = (self.object_key or "").strip()
            has_extension = "." in key_candidate.split("/")[-1] if key_candidate else False

            if has_extension:
                s3_key = key_candidate
            else:
                prefix = key_candidate
                if prefix and not prefix.endswith("/"):
                    prefix += "/"
                s3_key = f"{prefix}{uuid.uuid4()}.png"

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=data,
                ContentType=content_type,
                ACL=acl
            )

            s3_url = self._build_public_url(s3_key)
            logger.info(f"File uploaded to S3: {s3_url}")
            return s3_url
        except Exception as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise SophiaNetException(f"S3 upload error: {str(e)}", sys)

    def _build_public_url(self, key: str) -> str:
        region = self.s3_client.meta.region_name or "us-east-1"
        if region == "us-east-1":
            return f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
        return f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{key}"