from functools import lru_cache

from config.cloud import S3_BUCKET
from config.models import FALLBACK_IMAGE_MODEL, FLUX, IMAGE_MODEL, IMAGE_MODELS, STABLE_DIFFUSION
from utils.logger import logger


@lru_cache(maxsize=2)
def get_image_generator(model: IMAGE_MODELS):
    common = {
        "bucket_name": S3_BUCKET["AWS_S3_BUCKET_NAME"],
        "object_key": S3_BUCKET["AWS_S3_IMAGES_OBJECT_KEY"],
    }
    if model == IMAGE_MODELS.FLUX:
        from models.flux import Flux

        return Flux(**{key.lower(): value for key, value in FLUX.items()}, **common)
    from models.stable_diffusion import StableDiffusion

    return StableDiffusion(**{key.lower(): value for key, value in STABLE_DIFFUSION.items()}, **common)


def generate_image_with_fallback(prompt: str, session_history: list, files: list) -> tuple[dict, str]:
    models = list(dict.fromkeys([IMAGE_MODEL, FALLBACK_IMAGE_MODEL]))
    for index, model in enumerate(models):
        try:
            result = get_image_generator(model).generate_response(prompt, session_history, files)
            return result, model.value
        except Exception:
            if index == len(models) - 1:
                raise
            logger.warning("Image model %s failed; trying fallback %s", model.value, models[index + 1].value)
