import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app import app
from services.adk_summary import summarize


class ADKTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_adk_runner_and_request_isolation(self):
        results = await asyncio.gather(*[
            summarize(f"Source {i}", FakeListChatModel(responses=[f"Summary {i}"]))
            for i in range(2)
        ])
        self.assertEqual(results, ["Summary 0", "Summary 1"])

    def test_summary_api(self):
        with patch("services.adk_summary.summarize", new_callable=AsyncMock, return_value="Summary") as run:
            client = TestClient(app)
            response = client.post("/generate-summary", json={"prompt": "Source"})
            self.assertEqual(response.json()["engine"], "google-adk")
            self.assertEqual(response.json()["response"], "Summary")
            self.assertEqual(client.post("/generate-summary", json={"prompt": " "}).status_code, 400)
            run.assert_awaited_once_with("Source")
