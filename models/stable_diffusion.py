import sys
import boto3
import json
import base64
import io
from PIL import Image
from utils.logger import logger
from utils.exception import SophiaNetException
from utils.s3_syncer import S3Syncer

class StableDiffusion(S3Syncer):
    def __init__(self, model_id: str, runtime: str, region: str, bucket_name: str, object_key: str=""):
        self.model_id = model_id
        self.client = boto3.client(runtime, region_name=region)
        super().__init__(bucket_name, object_key)

    def generate_image(self, prompt: str):
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'prompt': prompt
                })
            )
            output_body = json.loads(response["body"].read().decode("utf-8"))
            base64_output_image = output_body["images"][0]
            image_data = base64.b64decode(base64_output_image)
            image = Image.open(io.BytesIO(image_data))
            return image
        except Exception as e:
            logger.error(f"Stable Diffusion error: {str(e)}")
            raise SophiaNetException(f"Stable Diffusion error: {str(e)}", sys)
    
    def generate_and_upload_image(self, prompt: str) -> str:
        try:
            image = self.generate_image(prompt)
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            s3_url = self.upload_file(img_byte_arr, content_type="image/png")
            return s3_url
        except Exception as e:
            logger.error(f"Error in generate_and_upload_image: {str(e)}")
            raise SophiaNetException(f"Error in generate_and_upload_image: {str(e)}", sys)