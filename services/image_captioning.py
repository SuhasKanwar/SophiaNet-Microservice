import sys
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance

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
    
    def denoise(self, image):
        """Apply Gaussian blur to reduce noise"""
        try:
            return image.filter(ImageFilter.GaussianBlur(radius=1))
        except Exception as e:
            logger.warning(f"Denoising failed: {str(e)}, returning original image")
            return image

    def adjust_contrast_and_noise(self, image):
        """Enhance contrast and brightness for better caption generation"""
        try:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.3)
            
            return image
        except Exception as e:
            logger.warning(f"Contrast adjustment failed: {str(e)}, returning original image")
            return image

    def detect_objects(self, image):
        """Apply edge detection to highlight objects"""
        try:
            edges = image.filter(ImageFilter.FIND_EDGES)
            
            return Image.blend(image, edges, alpha=0.2)
        except Exception as e:
            logger.warning(f"Object detection failed: {str(e)}, returning original image")
            return image

    def segment(self, image):
        """Apply basic segmentation using adaptive thresholding"""
        try:
            gray = image.convert('L')
            
            gray = ImageEnhance.Contrast(gray).enhance(1.5)
            
            segmented = Image.merge('RGB', (gray, gray, gray))
            
            return segmented
        except Exception as e:
            logger.warning(f"Segmentation failed: {str(e)}, returning original image")
            return image

    def preprocess_image(self, image):
        """Apply all preprocessing steps in sequence"""
        try:
            logger.info("Starting image preprocessing...")
            
            image = self.denoise(image)
            
            image = self.adjust_contrast_and_noise(image)
            
            image = self.detect_objects(image)
            
            image = self.segment(image)
            
            logger.info("Image preprocessing completed")
            return image
        except Exception as e:
            logger.error(f"Preprocessing failed: {str(e)}, using original image")
            return image

    def generate_caption(self, image_bytes: bytes, prompt=None) -> str:
        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            
            image = self.preprocess_image(image)
            
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