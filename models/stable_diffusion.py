import sys
import boto3
import json
import base64
import io
from PIL import Image
from config.models import STABLE_DIFFUSION
from utils.logger import logger
from utils.exception import SophiaNetException

class StableDiffusion():
    def __init__(self):
        self.model_id = STABLE_DIFFUSION["MODEL_ID"]
        self.client = boto3.client(STABLE_DIFFUSION["RUNTIME"], region_name=STABLE_DIFFUSION["REGION"])
    
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