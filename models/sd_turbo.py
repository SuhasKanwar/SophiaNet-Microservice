"""Local inference with generated PNGs uploaded directly from memory to S3."""

from io import BytesIO
from threading import Lock

from utils.metrics import Timer
from utils.s3_syncer import S3Syncer


class SDTurbo(S3Syncer):
    def __init__(self, model_id: str, revision: str, bucket_name: str, object_key: str):
        super().__init__(bucket_name, object_key)
        self.model_id = model_id
        self.revision = revision
        self._pipeline = None
        self._lock = Lock()

    def generate_response(self, prompt: str, session_history: list, files: list) -> dict:
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("An image description is required.")

        # The scheduler is mutable; serialize loading and inference on this CPU pipeline.
        with self._lock, Timer() as timer:
            import torch

            if self._pipeline is None:
                from diffusers import StableDiffusionPipeline

                pipeline = StableDiffusionPipeline.from_pretrained(
                    self.model_id,
                    revision=self.revision,
                    variant="fp16",
                    torch_dtype=torch.float32,
                    use_safetensors=True,
                    token=False,
                )
                pipeline.enable_attention_slicing()
                self._pipeline = pipeline.to("cpu")

            with torch.inference_mode():
                result = self._pipeline(
                    prompt=prompt, num_inference_steps=1, guidance_scale=0.0,
                    width=512, height=512,
                )
            if any(result.nsfw_content_detected or []):
                raise ValueError("The image was rejected by the model safety checker.")
            buffer = BytesIO()
            result.images[0].save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
            s3_url = self.upload_file(image_bytes, content_type="image/png")

        return {
            "s3_url": s3_url,
            "performance_metrics": {
                "latency_ms": timer.elapsed_ms,
                "image_size_bytes": len(image_bytes),
                "clip_score": None,
            },
        }
