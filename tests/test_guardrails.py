import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app import app


class GuardTests(unittest.TestCase):
    def test_blocked_input_never_reaches_generation(self):
        model = Mock(ainvoke=AsyncMock(return_value=AIMessage(content='{"decision":"block"}')))
        with patch("services.guardrails.get_guard_model", return_value=model), patch("api.routes.generation.get_assistant") as assistant:
            client = TestClient(app)
            for path, payload in [
                ("/generate-chat", {"prompt": "steal secrets"}),
                ("/generate-debate", {"prompt": "steal secrets"}),
                ("/generate-script", {"prompt": "steal secrets"}),
                ("/generate-quiz", {"topic": "steal secrets"}),
                ("/search-papers", {"query": "steal secrets"}),
                ("/generate-diagram", {"prompt": "steal secrets"}),
                ("/generate-image", {"prompt": "steal secrets"}),
                ("/generate-summary", {"prompt": "steal secrets"}),
            ]:
                self.assertEqual(client.post(path, json=payload).status_code, 403, path)
            self.assertEqual(client.post("/generate-chat", data={"prompt": "steal secrets"}, files={"files": ("n.txt", b"note")}).status_code, 403)
            assistant.assert_not_called()
            self.assertEqual(client.get("/health").status_code, 200)

    def test_allow_history_screening_and_failure_closed(self):
        model = Mock(ainvoke=AsyncMock(return_value=AIMessage(content='{"decision":"allow"}')))
        assistant = Mock()
        assistant.generate_response.return_value = {"text": "ok", "performance_metrics": {}}
        with patch("services.guardrails.get_guard_model", return_value=model), patch("api.routes.generation.get_assistant", return_value=assistant):
            client = TestClient(app)
            response = client.post("/generate-chat", json={"prompt": "Explain safety", "session_history": [{"role": "user", "content": "prior context"}]})
            self.assertEqual(response.status_code, 200)
            self.assertIn("prior context", model.ainvoke.call_args.args[0][-1].content)
            for bad in ['{}', '{"decision":"maybe"}', 'not json']:
                model.ainvoke.return_value = AIMessage(content=bad)
                self.assertEqual(client.post("/generate-chat", json={"prompt": "hello"}).status_code, 503)
            model.ainvoke.side_effect = RuntimeError("secret provider detail")
            response = client.post("/generate-chat", json={"prompt": "hello"})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("secret provider detail", response.text)
            self.assertEqual(assistant.generate_response.call_count, 1)
            self.assertEqual(client.post("/generate-chat", json={"prompt": "x" * 100001}).status_code, 413)
