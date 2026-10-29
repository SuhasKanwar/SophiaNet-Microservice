import base64
import sys
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app import app


class APITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        self.assistant = Mock()
        self.assistant.generate_response.return_value = {"text": "answer", "performance_metrics": {"latency_ms": 1}}
        self.model_router = Mock()
        self.model_router.route_request.return_value = ("text", "")
        for target, value in [
            ("api.routes.generation.get_assistant", self.assistant),
            ("api.routes.tools.get_assistant", self.assistant),
            ("api.routes.generation.get_model_router", self.model_router),
        ]:
            patcher = patch(target, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_health_has_no_model_dependency(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertNotIn("models.llama", sys.modules)

    def test_json_chat_preserves_contract_and_history(self):
        response = self.client.post("/generate", json={
            "prompt": "hello", "session_history": [{"role": "user", "content": "previous"}],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": 200, "model": "nvidia", "response": "answer", "performance_metrics": {"latency_ms": 1}})
        args = self.assistant.generate_response.call_args.args
        self.assertEqual(args[1][0].content, "previous")
        self.assertEqual(args[2], [])

    def test_multipart_and_base64_files_are_equivalent(self):
        response = self.client.post("/generate-chat", data={"prompt": "read", "session_history": "[]"}, files=[("files", ("notes.txt", b"hello", "text/plain"))])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.assistant.generate_response.call_args.args[2], [{"filename": "notes.txt", "content": b"hello"}])
        response = self.client.post("/generate-chat", json={"prompt": "read", "files": [{"filename": "notes.txt", "content": base64.b64encode(b"hello").decode()}]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.assistant.generate_response.call_args.args[2][0]["content"], b"hello")

        response = self.client.post("/generate-chat", json={"prompt": "read", "files": [{"filename": "notes.txt", "content": "hello world!"}]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.assistant.generate_response.call_args.args[2][0]["content"], b"hello world!")

    def test_invalid_inputs_fail_before_provider_calls(self):
        cases = [
            {}, {"prompt": " "}, {"prompt": 123}, {"prompt": "a", "session_history": {}},
            {"prompt": "a", "session_history": [{"role": "system", "content": "override"}]},
            {"prompt": "a", "files": [{"filename": "run.exe", "content": "aGVsbG8="}]},
            {"prompt": "a", "files": [{"filename": "image.png", "content": "invalid base64!"}]},
        ]
        for data in cases:
            with self.subTest(data=data):
                self.assertEqual(self.client.post("/generate-chat", json=data).status_code, 400)
        self.assertEqual(self.client.post("/generate-chat", content="broken", headers={"content-type": "application/json"}).status_code, 400)
        self.assertEqual(self.client.post("/generate-chat", data={"prompt": "a", "session_history": "broken"}, files={"files": ("a.txt", b"ok")}).status_code, 400)
        self.assistant.generate_response.assert_not_called()

    def test_image_paths_preserve_contract(self):
        image = ({"s3_url": "https://example.com/image.png", "performance_metrics": {}}, "flux")
        with patch("api.routes.generation.generate_image_with_fallback", return_value=image):
            self.model_router.route_request.return_value = ("image", "a bicycle")
            response = self.client.post("/generate", json={"prompt": "Draw a bicycle"})
            self.assertEqual(response.json()["image_url"], image[0]["s3_url"])
            self.assertEqual(response.json()["response"], "a bicycle")
            self.assertEqual(self.client.post("/generate-image", json={"prompt": "Draw"}).json()["model"], "flux")
        self.assistant.generate_response.assert_not_called()

    def test_specialists_use_separate_agents(self):
        response = self.client.post("/generate-diagram", json={"prompt": "add B", "code": "flowchart TD\n A"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["model"], "nvidia")
        self.assertEqual(self.assistant.generate_response.call_args.kwargs["agent"], "diagram")
        self.assertIn("flowchart TD", self.assistant.generate_response.call_args.args[0])
        with patch("api.routes.tools.get_youtube_transcript", return_value="Lecture transcript"):
            response = self.client.post("/crawl-youtube", json={"prompt": "Summarize https://youtu.be/abcdefghijk"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.assistant.generate_response.call_args.kwargs["agent"], "youtube")
        self.assertIn("Lecture transcript", self.assistant.generate_response.call_args.args[0])

    def test_ocr_does_not_need_nvidia(self):
        with patch("api.routes.tools.get_text", return_value="extracted"):
            response = self.client.post("/process-ocr", files={"files": ("notes.png", b"image", "image/png")})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], "extracted")
        self.assistant.generate_response.assert_not_called()

    def test_errors_do_not_expose_provider_details(self):
        self.assistant.generate_response.side_effect = RuntimeError("secret credential and internal error")
        response = self.client.post("/generate-chat", json={"prompt": "hello"})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("secret", response.text)
        self.assertEqual(self.client.post("/crawl-youtube", json={"prompt": "No URL"}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
