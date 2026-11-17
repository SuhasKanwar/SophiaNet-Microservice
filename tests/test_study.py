import json
import unittest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from pydantic import ValidationError
from app import app
from services.study import StudyService


def valid_quiz():
    return {'title':'Practice','questions':[{'question':f'Question {i}?','options':['A','B','C','D'],'answer':1,'explanation':'Because B.'} for i in range(3)]}


class StudyTests(unittest.TestCase):
    def service(self, data):
        model = Mock(); model.bind.return_value = model
        model.invoke.return_value = AIMessage(content=json.dumps(data))
        return StudyService(model)

    def test_output_validation(self):
        self.assertEqual(self.service(valid_quiz()).generate('topic').questions[0].answer,1)
        for field,value in [('answer',4),('options',['a','a','b','c']),('explanation','')]:
            data=valid_quiz();data['questions'][0][field]=value
            with self.assertRaises(ValidationError): self.service(data).generate('topic')
        data=valid_quiz();data['questions']=[]
        with self.assertRaises(ValidationError): self.service(data).generate('topic')

    def test_endpoint_contract_and_input_limits(self):
        with patch('api.routes.study.get_study',return_value=self.service(valid_quiz())),TestClient(app) as client:
            self.assertEqual(len(client.post('/generate-quiz',json={'topic':'math'}).json()['quiz']['questions']),3)
            for topic in ['', ' ', 'x'*10001]:
                self.assertEqual(client.post('/generate-quiz',json={'topic':topic}).status_code,422)

    def test_invalid_model_output_gets_one_correction_attempt(self):
        model = Mock(); model.bind.return_value = model
        model.invoke.side_effect = [AIMessage(content='{"$defs": {}}'), AIMessage(content=json.dumps(valid_quiz()))]
        self.assertEqual(len(StudyService(model).generate('topic').questions),3)
        self.assertEqual(model.invoke.call_count,2)

    def test_flashcards_validation_and_api(self):
        deck={'title':'Recall','cards':[{'front':f'Question {i}?','back':f'Answer {i}'} for i in range(5)]}
        service=self.service(deck)
        self.assertEqual(len(service.flashcards('topic').cards),5)
        with patch('api.routes.study.get_study',return_value=service),TestClient(app) as client:
            response=client.post('/generate-flashcards',json={'topic':'water cycle'})
            self.assertEqual(response.status_code,200)
            self.assertEqual(len(response.json()['deck']['cards']),5)
        for cards in ([],[{'front':'Same','back':'Answer'}]*5,[{'front':' ','back':'Answer'}]*5):
            with self.assertRaises(ValidationError):self.service({'title':'Recall','cards':cards}).flashcards('topic')
