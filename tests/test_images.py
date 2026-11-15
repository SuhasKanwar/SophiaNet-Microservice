import base64
from io import BytesIO
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PIL import Image

from config.models import IMAGE_MODEL, FALLBACK_IMAGE_MODEL, IMAGE_MODELS, SD_TURBO
from models.sd_turbo import SDTurbo
from services.images import generate_image_with_fallback


class LocalImageTests(unittest.TestCase):
    def test_defaults_never_use_paid_provider_even_on_failure(self):
        self.assertEqual(IMAGE_MODEL, IMAGE_MODELS.SD_TURBO)
        self.assertEqual(FALLBACK_IMAGE_MODEL, IMAGE_MODELS.SD_TURBO)
        with patch('services.images.get_image_generator', side_effect=RuntimeError('offline')) as factory:
            with self.assertRaisesRegex(RuntimeError, 'offline'):
                generate_image_with_fallback('a cat', [], [])
        factory.assert_called_once_with(IMAGE_MODELS.SD_TURBO)

    def test_png_contract_and_full_prompt(self):
        model = SDTurbo(**{key.lower(): value for key, value in SD_TURBO.items()})
        model._pipeline = Mock(return_value=SimpleNamespace(images=[Image.new('RGB', (512, 512), 'blue')], nsfw_content_detected=None))
        prompt = 'A detailed illustration of a garden with a stream and bridge. ' * 4
        result = model.generate_response(prompt, [], [])
        image_bytes = base64.b64decode(result['image_url'].split(',', 1)[1])
        self.assertEqual(Image.open(BytesIO(image_bytes)).size, (512, 512))
        self.assertEqual(result['performance_metrics']['image_size_bytes'], len(image_bytes))
        self.assertIsNone(result['performance_metrics']['clip_score'])
        model._pipeline.assert_called_once_with(prompt=prompt.strip(), num_inference_steps=1, guidance_scale=0.0, width=512, height=512)

    def test_empty_prompt_rejected_before_loading(self):
        model = SDTurbo('unused', 'unused')
        with self.assertRaises(ValueError):
            model.generate_response('  ', [], [])
        self.assertIsNone(model._pipeline)

    def test_flagged_output_is_not_returned(self):
        model = SDTurbo('unused', 'unused')
        model._pipeline = Mock(return_value=SimpleNamespace(images=[], nsfw_content_detected=[True]))
        with self.assertRaisesRegex(ValueError, 'safety checker'):
            model.generate_response('a prompt', [], [])
