import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from app import app
from services.guardrails import guard_request


class ScriptTests(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides[guard_request] = lambda: None
        self.addCleanup(app.dependency_overrides.pop, guard_request, None)
    def test_transport_and_real_crew(self):
        from services.scripts import generate_script
        model = FakeListChatModel(responses=['Final Answer: Draft script', 'Final Answer: Edited script'])
        result = generate_script('A short scene about rain', 'narration', model=model)
        self.assertIn('Edited script', result)

    def test_route_validation_and_contract(self):
        with TestClient(app) as client, patch('services.scripts.generate_script', return_value='A script'):
            response = client.post('/generate-script', json={'prompt': 'rain'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['response'], 'A script')
            for body in ({'prompt':' '}, {'prompt':'test','kind':'bad'}):
                self.assertEqual(client.post('/generate-script',json=body).status_code,422)
