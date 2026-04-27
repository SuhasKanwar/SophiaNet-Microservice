import sys
from io import BytesIO
from PIL import Image

import torch
from transformers import CLIPProcessor, CLIPModel

from utils.logger import logger
from utils.exception import SophiaNetException
from config.models import CLIP_MODEL


class ClipService:
    def __init__(self, model_name: str, processor_name: str):
        self.model_name = model_name
        self.processor_name = processor_name
        try:
            self.model = CLIPModel.from_pretrained(model_name)
            self.processor = CLIPProcessor.from_pretrained(processor_name)
            self.model.eval()
            logger.info(f"CLIP model loaded: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {str(e)}")
            raise SophiaNetException(f"Failed to load CLIP model ({model_name})", sys)

    def compute_clip_score(self, prompt: str, image_bytes: bytes) -> float | None:
        """Compute cosine similarity between a text prompt and an image using CLIP."""
        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            inputs = self.processor(text=[prompt], images=image, return_tensors="pt", padding=True)

            with torch.no_grad():
                outputs = self.model(**inputs)

            # Normalised cosine similarity (0-1 scale)
            score = outputs.logits_per_image.squeeze().item() / 100.0
            return round(max(0.0, min(1.0, score)), 4)
        except Exception as e:
            logger.warning(f"CLIP score computation failed: {str(e)}")
            return None


# Module-level singleton — loaded once at startup
clip_service = ClipService(
    model_name=CLIP_MODEL["MODEL_NAME"],
    processor_name=CLIP_MODEL["PROCESSOR"],
)