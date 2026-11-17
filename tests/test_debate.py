import json
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from agents.debate import build_debate
from app import app
from tools.review_tools import calculate


class DebateTests(unittest.IsolatedAsyncioTestCase):
    async def test_panel_order_and_final_answer(self):
        graph = build_debate(FakeListChatModel(responses=['proposal', 'correction', 'synthesis']), [])
        updates = [event async for event in graph.astream({'messages': [('user', 'question')]}, stream_mode='updates')]
        self.assertEqual([next(iter(item)) for item in updates], ['advocate', 'critic', 'judge'])
        self.assertEqual(updates[-1]['judge']['judge'], 'synthesis')

    def test_stream_contract_and_errors(self):
        graph = build_debate(FakeListChatModel(responses=['proposal', 'correction', 'synthesis']), [])
        with patch('api.routes.debate.get_debate', return_value=graph), TestClient(app) as client:
            response = client.post('/generate-debate', json={'prompt': 'question'})
            events = [json.loads(line) for line in response.text.splitlines()]
            self.assertEqual(events[-1]['type'], 'done')
            self.assertEqual(events[-1]['text'], 'synthesis')
            self.assertEqual(client.post('/generate-debate', json={'prompt': ''}).status_code, 400)
        with patch('api.routes.debate.get_debate', side_effect=RuntimeError('secret')), TestClient(app) as client:
            response = client.post('/generate-debate', json={'prompt': 'question'})
            self.assertEqual(json.loads(response.text.splitlines()[-1])['type'], 'error')
            self.assertNotIn('secret', response.text)

    def test_calculator_rejects_code_and_unbounded_operations(self):
        self.assertEqual(calculate.invoke({'expression': '(12 + 8) / 4'}), '5.0')
        for expression in ['__import__("os")', '2 ** 100000', '1 / 0', '9' * 201]:
            with self.assertRaises((ValueError, ZeroDivisionError)):
                calculate.invoke({'expression': expression})

    def test_command_contract(self):
        graph = build_debate(FakeListChatModel(responses=['proposal','critique','final']), [])
        with patch('api.routes.debate.get_debate',return_value=graph),TestClient(app) as client:
            result=client.post('/generate-debate',json={'prompt':'question','command':'agent-battleground'})
            self.assertEqual(json.loads(result.text.splitlines()[-1])['type'],'done')
            self.assertEqual(client.post('/generate-debate',json={'prompt':'question','command':'unknown'}).status_code,400)
            self.assertEqual(client.post('/generate-debate',json={'prompt':'','command':'agent-battleground'}).status_code,400)
            self.assertEqual(client.post('/generate',json={'prompt':'question','command':'agent-battleground'}).status_code,400)
