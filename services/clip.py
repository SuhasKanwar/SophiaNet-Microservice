import sys
import torch
from io import BytesIO
from PIL import Image
from typing import Union, List
import numpy as np

from transformers import CLIPProcessor, CLIPModel

from utils.logger import logger
from utils.exception import SophiaNetException

class ClipService:
    def __init__(self, model_name: str, processor_name: str):
        try:
            logger.info(f"Loading CLIP model: {model_name}")
            self.model_name = model_name
            self.processor = CLIPProcessor.from_pretrained(processor_name)
            self.model = CLIPModel.from_pretrained(model_name)
            self.model.eval()
            logger.info("CLIP model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {str(e)}")
            raise SophiaNetException(f"Failed to load CLIP model: {str(e)}", sys)
    
    def encode_text(self, text: Union[str, List[str]]) -> np.ndarray:
        try:
            if isinstance(text, str):
                text = [text]
            
            inputs = self.processor(text=text, return_tensors="pt", padding=True, truncation=True)
            
            with torch.no_grad():
                text_features = self.model.get_text_features(**inputs)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            embeddings = text_features.cpu().numpy()
            logger.info(f"Encoded {len(text)} text(s) into embeddings of shape {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.error(f"Text encoding error: {str(e)}")
            raise SophiaNetException(f"Text encoding error: {str(e)}", sys)
    
    def encode_image(self, image_input: Union[bytes, Image.Image, List[Union[bytes, Image.Image]]]) -> np.ndarray:
        try:
            if not isinstance(image_input, list):
                image_input = [image_input]
            
            images = []
            for img in image_input:
                if isinstance(img, bytes):
                    img = Image.open(BytesIO(img)).convert("RGB")
                elif isinstance(img, Image.Image):
                    img = img.convert("RGB")
                else:
                    raise ValueError(f"Unsupported image type: {type(img)}")
                images.append(img)
            
            inputs = self.processor(images=images, return_tensors="pt", padding=True)
            
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
                # Normalize embeddings
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            embeddings = image_features.cpu().numpy()
            logger.info(f"Encoded {len(images)} image(s) into embeddings of shape {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.error(f"Image encoding error: {str(e)}")
            raise SophiaNetException(f"Image encoding error: {str(e)}", sys)
    
    def compute_similarity(self, text_embeddings: np.ndarray, image_embeddings: np.ndarray) -> np.ndarray:
        try:
            similarity = np.dot(text_embeddings, image_embeddings.T)
            
            similarity = (similarity + 1) / 2
            
            logger.info(f"Computed similarity matrix of shape {similarity.shape}")
            return similarity
        except Exception as e:
            logger.error(f"Similarity computation error: {str(e)}")
            raise SophiaNetException(f"Similarity computation error: {str(e)}", sys)
    
    def find_best_match(self, query: str, image_inputs: List[Union[bytes, Image.Image]]) -> int:
        try:
            text_embedding = self.encode_text(query)
            image_embeddings = self.encode_image(image_inputs)
            
            similarities = self.compute_similarity(text_embedding, image_embeddings)
            best_idx = np.argmax(similarities[0])
            
            logger.info(f"Best match for query '{query}' is image at index {best_idx} with similarity {similarities[0][best_idx]:.4f}")
            return int(best_idx)
        except Exception as e:
            logger.error(f"Best match search error: {str(e)}")
            raise SophiaNetException(f"Best match search error: {str(e)}", sys)