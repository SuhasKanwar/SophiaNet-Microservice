from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch

from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.messages import AIMessage

from services.assistant import AssistantService
from services.rag import RAGService, get_embeddings


class ContextModel:
    def invoke(self, messages):
        return AIMessage(content="\n".join(message.content for message in messages))


class RetrievalTests(unittest.TestCase):
    def test_concurrent_file_requests_keep_separate_context(self):
        assistant = AssistantService(model=ContextModel(), tools=[])
        files = [
            [{"filename": "alice.txt", "content": b"Alice private document"}],
            [{"filename": "bob.txt", "content": b"Bob private document"}],
        ]
        with patch("services.rag.get_embeddings", return_value=DeterministicFakeEmbedding(size=8)):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda payload: assistant.generate_response("Summarize", [], payload), files))
        self.assertIn("Alice private", results[0]["text"])
        self.assertNotIn("Bob private", results[0]["text"])
        self.assertIn("Bob private", results[1]["text"])
        self.assertNotIn("Alice private", results[1]["text"])
        self.assertEqual(results[0]["performance_metrics"]["chunks_retrieved"], 1)
        self.assertNotIn("Alice private", assistant.generate_response("Hello", [], [])["text"])

    def test_public_embeddings_use_cpu_without_implicit_credentials(self):
        get_embeddings.cache_clear()
        self.addCleanup(get_embeddings.cache_clear)
        with patch("services.rag.HuggingFaceEmbeddings") as factory:
            self.assertIs(get_embeddings(), get_embeddings())
        factory.assert_called_once()
        self.assertEqual(factory.call_args.kwargs["model_kwargs"], {"token": False, "device": "cpu"})

    def test_retrieval_errors_are_not_silently_ignored(self):
        rag = RAGService()
        with patch("utils.files.process_files", side_effect=ValueError("bad file")):
            with self.assertRaisesRegex(ValueError, "bad file"):
                rag._ingest_files([{"filename": "bad.pdf", "content": b"broken"}])


if __name__ == "__main__":
    unittest.main()
