import os
import unittest
from unittest.mock import Mock, patch

from langchain_core.messages import AIMessage
from pydantic import ValidationError

from config.models import NVIDIA
from models.nvidia import create_nvidia_model
from services.images import generate_image_with_fallback
from services.router import ModelRouter
from tools.custom_tools import scrape_website, validate_public_url


class ProviderTests(unittest.TestCase):
    def test_nvidia_transport_and_configuration(self):
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
            model = create_nvidia_model()
        self.assertEqual(str(model.root_client.base_url), "https://integrate.api.nvidia.com/v1/")
        self.assertEqual(model.model_name, NVIDIA["MODEL_NAME"])
        self.assertNotIn("llama", model.model_name.lower())
        self.assertFalse(model.use_responses_api)
        self.assertFalse(model.extra_body["chat_template_kwargs"]["enable_thinking"])
        with patch.dict(os.environ, {"NVIDIA_API_KEY": ""}):
            with self.assertRaisesRegex(RuntimeError, "NVIDIA_API_KEY"):
                create_nvidia_model()

    def test_router_validates_provider_json(self):
        model = Mock()
        model.bind.return_value = model
        router = ModelRouter(model=model)
        for classification in ("text", "image"):
            model.invoke.return_value = AIMessage(content=f'{{"classification": "{classification}"}}')
            self.assertEqual(router.route_request("prompt"), (classification, ""))
        for content in ('{"classification":"llama"}', 'not json', '{"classification":"text", "extra":"bad"}'):
            model.invoke.return_value = AIMessage(content=content)
            with self.assertRaises(ValidationError):
                router.route_request("prompt")

    def test_fallback_includes_initialization_failures(self):
        fallback = Mock()
        fallback.generate_response.return_value = {"s3_url": "image"}
        with patch("services.images.get_image_generator", side_effect=[RuntimeError("primary unavailable"), fallback]) as factory:
            result, model = generate_image_with_fallback("draw", [], [])
        self.assertEqual(result, {"s3_url": "image"})
        self.assertEqual(model, "stable_diffusion")
        self.assertEqual(factory.call_count, 2)
        with patch("services.images.get_image_generator", side_effect=RuntimeError("all unavailable")):
            with self.assertRaisesRegex(RuntimeError, "all unavailable"):
                generate_image_with_fallback("draw", [], [])


class WebsiteToolTests(unittest.TestCase):
    def test_private_addresses_and_non_http_urls_are_rejected(self):
        for url in ("file:///etc/passwd", "ftp://example.com", "https://user:pass@example.com"):
            with self.assertRaises(ValueError):
                validate_public_url(url)
        for address in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "::1"):
            with patch("tools.custom_tools.socket.getaddrinfo", return_value=[(None, None, None, None, (address, 80))]):
                with self.assertRaises(ValueError):
                    validate_public_url("https://example.com")

    def test_scrape_returns_text_and_source(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.is_redirect = False
        response.headers = {"Content-Type": "text/html"}
        response.iter_content.return_value = [b"<html><script>ignore me</script><p>Evidence</p></html>"]
        with patch("tools.custom_tools.validate_public_url"), patch("tools.custom_tools.requests.get", return_value=response):
            result = scrape_website.invoke({"url": "https://example.com"})
        self.assertIn("Source: https://example.com", result)
        self.assertIn("Evidence", result)
        self.assertNotIn("ignore me", result)

    def test_redirect_is_validated_before_fetch(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.is_redirect = True
        response.headers = {"Location": "http://127.0.0.1/private"}
        with patch("tools.custom_tools.validate_public_url", side_effect=[None, ValueError("private")]), patch("tools.custom_tools.requests.get", return_value=response) as fetch:
            with self.assertRaisesRegex(ValueError, "private"):
                scrape_website.invoke({"url": "https://example.com"})
        self.assertEqual(fetch.call_count, 1)


if __name__ == "__main__":
    unittest.main()
