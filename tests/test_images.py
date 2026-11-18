from io import BytesIO
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PIL import Image

from config.models import IMAGE_MODEL, FALLBACK_IMAGE_MODEL, IMAGE_MODELS, SD_TURBO
from models.sd_turbo import SDTurbo
from services.images import generate_image_with_fallback


class LocalImageTests(unittest.TestCase):
    def setUp(self):
        client = patch('utils.s3_syncer.boto3.client')
        client.start()
        self.addCleanup(client.stop)

    def make_model(self):
        return SDTurbo(**{key.lower(): value for key, value in SD_TURBO.items()}, bucket_name='test-bucket', object_key='generated-images/')

    def test_defaults_never_use_paid_provider_even_on_failure(self):
        self.assertEqual(IMAGE_MODEL, IMAGE_MODELS.SD_TURBO)
        self.assertEqual(FALLBACK_IMAGE_MODEL, IMAGE_MODELS.SD_TURBO)
        with patch('services.images.get_image_generator', side_effect=RuntimeError('offline')) as factory:
            with self.assertRaisesRegex(RuntimeError, 'offline'):
                generate_image_with_fallback('a cat', [], [])
        factory.assert_called_once_with(IMAGE_MODELS.SD_TURBO)

    def test_png_contract_and_full_prompt(self):
        model = self.make_model()
        model._pipeline = Mock(return_value=SimpleNamespace(images=[Image.new('RGB', (512, 512), 'blue')], nsfw_content_detected=None))
        prompt = 'A detailed illustration of a garden with a stream and bridge. ' * 4
        model.upload_file = Mock(return_value='https://test-bucket.s3.amazonaws.com/generated-images/test.png')
        result = model.generate_response(prompt, [], [])
        image_bytes = model.upload_file.call_args.args[0]
        self.assertEqual(result['s3_url'], model.upload_file.return_value)
        self.assertNotIn('image_url', result)
        model.upload_file.assert_called_once_with(image_bytes, content_type='image/png')
        self.assertEqual(Image.open(BytesIO(image_bytes)).size, (512, 512))
        self.assertEqual(result['performance_metrics']['image_size_bytes'], len(image_bytes))
        self.assertIsNone(result['performance_metrics']['clip_score'])
        model._pipeline.assert_called_once_with(prompt=prompt.strip(), num_inference_steps=1, guidance_scale=0.0, width=512, height=512)

    def test_empty_prompt_rejected_before_loading(self):
        model = self.make_model()
        with self.assertRaises(ValueError):
            model.generate_response('  ', [], [])
        self.assertIsNone(model._pipeline)

    def test_flagged_output_is_not_returned(self):
        model = self.make_model()
        model._pipeline = Mock(return_value=SimpleNamespace(images=[], nsfw_content_detected=[True]))
        with self.assertRaisesRegex(ValueError, 'safety checker'):
            model.generate_response('a prompt', [], [])

    def test_s3_failure_does_not_return_inline_or_local_image(self):
        model = self.make_model()
        model._pipeline = Mock(return_value=SimpleNamespace(images=[Image.new('RGB',(512,512),'blue')],nsfw_content_detected=None))
        model.upload_file = Mock(side_effect=RuntimeError('S3 unavailable'))
        with self.assertRaisesRegex(RuntimeError,'S3 unavailable'):
            model.generate_response('a lake',[],[])
