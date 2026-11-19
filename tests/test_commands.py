import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient

from app import app
from services.guardrails import guard_request
from services.study import Quiz, FlashcardDeck


class CommandTests(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[guard_request] = lambda: None
        self.addCleanup(app.dependency_overrides.pop, guard_request, None)
        self.client = TestClient(app)

    def test_dispatches_summary_study_and_research(self):
        with patch('services.adk_summary.summarize', new_callable=AsyncMock, return_value='Summary') as run:
            response = self.client.post('/generate', json={'command': 'summarize', 'prompt': 'Source'})
            self.assertEqual(response.json()['engine'], 'google-adk')
            self.assertEqual(response.json()['response'], 'Summary')
            run.assert_awaited_once_with('Source')
        study = Mock()
        study.generate.return_value = Quiz(title='Quiz', questions=[dict(question=f'Question {i}', options=['a','b','c','d'], answer=1, explanation='Because') for i in range(3)])
        study.flashcards.return_value = FlashcardDeck(title='Deck', cards=[dict(front=f'Question {i}', back='Answer') for i in range(5)])
        with patch('services.study.get_study', return_value=study):
            for command, expected in [('quiz', '**Answer: B.**'), ('flashcards', '### Question 4')]:
                result = self.client.post('/generate', json={'command': command, 'prompt': 'Physics'}).json()
                self.assertIn(expected, result['response'])
                self.assertEqual(result['command'], command)
        paper = dict(title='A paper', year=2025, venue='A journal', relevance='Relevant', url='https://arxiv.org/abs/1234')
        with patch('services.paper_research.research_papers', return_value={'papers':[paper]}) as research:
            result = self.client.post('/generate', json={'command':'research', 'prompt':'retrieval'}).json()
            self.assertIn(paper['url'], result['response'])
            research.assert_called_once_with('retrieval', None, 5)

    def test_rejects_unknown_empty_misrouted_and_attached_commands(self):
        for payload in [
            {'command':'unknown','prompt':'question'},
            {'command':'summarize','prompt':''},
            {'command':'research','prompt':'x'*501},
            {'command':'quiz','prompt':'topic','files':[{'filename':'n.txt','content':'source!'}]},
        ]:
            self.assertEqual(self.client.post('/generate', json=payload).status_code,400)
        self.assertEqual(self.client.post('/generate-debate', json={'command':'quiz','prompt':'topic'}).status_code,400)
