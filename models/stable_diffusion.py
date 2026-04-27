import sys
import boto3
import json
import base64
import io
import re
from PIL import Image

from utils.logger import logger
from utils.exception import SophiaNetException
from utils.s3_syncer import S3Syncer
from utils.metrics import Timer
from services.rag import RAGService
from services.clip import clip_service

from config.prompts import STABLE_DIFFUSION_SYSTEM_PROMPT

class StableDiffusion(S3Syncer, RAGService):
    def __init__(self, model_id: str, runtime: str, region: str, max_tokens: int, bucket_name: str, object_key: str="", chunk_size: int=1000, chunk_overlap: int=150):
        S3Syncer.__init__(self, bucket_name=bucket_name, object_key=object_key)
        RAGService.__init__(self, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.model_id = model_id
        self.client = boto3.client(runtime, region_name=region)
        self.max_tokens = max_tokens
        self.system_prompt = STABLE_DIFFUSION_SYSTEM_PROMPT

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

    def generate_image(self, prompt: str):
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'prompt': prompt
                })
            )
            output_body = json.loads(response["body"].read().decode("utf-8"))

            finish_reasons = output_body.get("finish_reasons", []) or []
            if any("filter reason: prompt" in str(reason).lower() for reason in finish_reasons):
                raise Exception("Prompt blocked by model safety filters (finish reason: prompt)")
            
            base64_output_image = None
            
            if "images" in output_body and output_body["images"]:
                base64_output_image = output_body["images"][0]
            elif "artifacts" in output_body and output_body["artifacts"]:
                base64_output_image = output_body["artifacts"][0].get("base64")
            elif "result" in output_body:
                base64_output_image = output_body["result"]
            else:
                logger.error(f"Unexpected response format: {output_body}")
                raise Exception(f"Unexpected response format. Available keys: {list(output_body.keys())}")
            
            if not base64_output_image:
                raise Exception("No image data found in the response")
                
            image_data = base64.b64decode(base64_output_image)
            image = Image.open(io.BytesIO(image_data))
            return image
        except Exception as e:
            logger.error(f"Stable Diffusion error: {str(e)}")
            raise SophiaNetException(f"Stable Diffusion error: {str(e)}", sys)

    def _compute_metrics(self, prompt_used: str, image_bytes: bytes, latency_ms: float) -> dict:
        return {
            "latency_ms": latency_ms,
            "clip_score": clip_service.compute_clip_score(prompt_used, image_bytes),
            "image_size_bytes": len(image_bytes),
        }
    
    def generate_response(self, prompt: str, session_history: list, files: list) -> dict:
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
                    if "Prompt blocked by model safety filters" not in str(model_error):
                        raise
                    logger.warning("Stable Diffusion prompt filtered; retrying once with safer fallback prompt")
                    safe_prompt = self._fallback_safe_prompt(sanitized_prompt)
                    image = self.generate_image(safe_prompt)

                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                s3_url = self.upload_file(img_bytes, content_type="image/png")

            metrics = self._compute_metrics(sanitized_prompt, img_bytes, t.elapsed_ms)
            return {"s3_url": s3_url, "performance_metrics": metrics}
        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            raise SophiaNetException(f"Error in generate_response: {str(e)}", sys)