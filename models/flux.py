import os
import sys
import io
import re

from PIL import Image
from huggingface_hub import InferenceClient

from utils.logger import logger
from utils.exception import SophiaNetException
from utils.s3_syncer import S3Syncer
from utils.metrics import Timer
from services.rag import RAGService
from services.clip import clip_service

from config.prompts import FLUX_SYSTEM_PROMPT


class Flux(S3Syncer, RAGService):
    def __init__(
        self,
        model_id: str,
        provider: str,
        max_tokens: int,
        bucket_name: str,
        object_key: str = "",
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ):
        S3Syncer.__init__(self, bucket_name=bucket_name, object_key=object_key)
        RAGService.__init__(self, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.model_id = model_id
        self.provider = provider
        self.max_tokens = max_tokens
        self.system_prompt = FLUX_SYSTEM_PROMPT
        self.client = InferenceClient(
            provider=self.provider,
            api_key=os.getenv("HF_TOKEN"),
        )

    @staticmethod
    def _sanitize_prompt(prompt: str) -> str:
        if not prompt:
            return ""

        sanitized_prompt = prompt.strip()
        sanitized_prompt = re.sub(r"^\s*(human|assistant|system)\s*:\s*", "", sanitized_prompt, flags=re.IGNORECASE)
        sanitized_prompt = sanitized_prompt.replace("```", "")
        sanitized_prompt = re.sub(r"\s+", " ", sanitized_prompt).strip()
        return sanitized_prompt

    def _trim_prompt(self, prompt: str) -> str:
        if not prompt:
            return ""

        if len(prompt) <= self.max_tokens:
            return prompt

        trimmed_prompt = prompt[:self.max_tokens].rsplit(" ", 1)[0].strip()
        return trimmed_prompt or prompt[:self.max_tokens]

    def _fallback_safe_prompt(self, prompt: str) -> str:
        base_prompt = self._sanitize_prompt(prompt)
        base_prompt = self._trim_prompt(base_prompt)

        if not base_prompt:
            return "A clean, abstract, colorful digital artwork with no text."

        return (
            f"Create a safe-for-work, non-violent, non-explicit digital illustration of: {base_prompt}. "
            "No gore, no nudity, no hateful content, no illegal activity, no text overlays."
        )

    def generate_image(self, prompt: str) -> Image.Image:
        try:
            image = self.client.text_to_image(
                prompt,
                model=self.model_id,
            )

            if not isinstance(image, Image.Image):
                raise Exception("Unexpected response type from Flux image generation")

            return image
        except Exception as e:
            logger.error(f"Flux generation error: {str(e)}")
            raise SophiaNetException(f"Flux generation error: {str(e)}", sys)

    def _compute_metrics(self, prompt_used: str, image_bytes: bytes, latency_ms: float) -> dict:
        """Compute image-generation performance metrics internally."""
        return {
            "latency_ms": latency_ms,
            "clip_score": clip_service.compute_clip_score(prompt_used, image_bytes),
            "image_size_bytes": len(image_bytes),
        }

    def generate_response(self, prompt: str, session_history: list, files: list) -> dict:
        """Return {"s3_url": str, "performance_metrics": dict}."""
        try:
            with Timer() as t:
                self._ingest_files(files)
                _ = self._retrieve_context(prompt)
                _ = session_history or []

                sanitized_prompt = self._sanitize_prompt(prompt)
                sanitized_prompt = self._trim_prompt(sanitized_prompt)

                if not sanitized_prompt:
                    raise Exception("Prompt is empty after sanitization")

                try:
                    image = self.generate_image(sanitized_prompt)
                except SophiaNetException as model_error:
                    logger.warning(f"Flux prompt retry with safe fallback due to: {str(model_error)}")
                    safe_prompt = self._fallback_safe_prompt(sanitized_prompt)
                    image = self.generate_image(safe_prompt)

                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format="PNG")
                img_bytes = img_byte_arr.getvalue()

                s3_url = self.upload_file(img_bytes, content_type="image/png")

            metrics = self._compute_metrics(sanitized_prompt, img_bytes, t.elapsed_ms)
            return {"s3_url": s3_url, "performance_metrics": metrics}
        except Exception as e:
            logger.error(f"Error in Flux generate_response: {str(e)}")
            raise SophiaNetException(f"Error in Flux generate_response: {str(e)}", sys)
