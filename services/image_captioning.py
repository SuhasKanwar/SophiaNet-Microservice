import sys
from io import BytesIO
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

from utils.logger import logger
from utils.exception import SophiaNetException

class ImageCaptioningService:
    def __init__(self, model_name, task, processor_name):
        self.model_name = model_name
        self.task = task
        self.processor_name = processor_name
        self.processor = BlipProcessor.from_pretrained(processor_name, use_fast=True)
        self.model = BlipForConditionalGeneration.from_pretrained(model_name)
    
    def generate_caption(self, image_bytes: bytes, prompt=None) -> str:
        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            if prompt:
                inputs = self.processor(image, prompt, return_tensors="pt")
            else:
                inputs = self.processor(image, return_tensors="pt")
            
            out = self.model.generate(
                **inputs,
                max_new_tokens=50
            )
            caption = self.processor.decode(out[0], skip_special_tokens=True)
            logger.info(f"Generated caption: {caption}")
            return caption
        except Exception as e:
            logger.error(f"Image Captioning error: {str(e)}")
            raise SophiaNetException(f"Image Captioning error: {str(e)}", sys)