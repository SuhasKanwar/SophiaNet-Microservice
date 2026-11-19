import unittest
from unittest.mock import Mock, patch

from evaluation.score import score
from evaluation.run import execute


class EvaluationTests(unittest.TestCase):
    def case(self, scorer, reference=None):
        return dict(id='test',group='test',persona='novice',prompt_style='direct',endpoint='/generate-chat',payload={},scorer=scorer,reference=reference or {},expected_status=200)

    def test_numeric_requires_final_marker_and_exact_answer(self):
        case=self.case('numeric',{'answer':'18'})
        for text,expected in [('There were 18 apples; FINAL_ANSWER: 19',False),('The answer is 18',False),('**FINAL_ANSWER: 18**',True),('FINAL_ANSWER: 180',False)]:
            self.assertEqual(score(case,200,{'response':text})['numeric_exact_match'],expected)

    def test_fact_checks_are_word_bounded_and_allow_aliases(self):
        case=self.case('facts',{'facts':[['7','seven'],['Mira']]})
        self.assertTrue(all(score(case,200,{'response':'Mira has seven books.'}).values()))
        self.assertFalse(all(score(case,200,{'response':'Miranda has 17 books.'}).values()))

    def test_unavailable_provider_is_not_scored_as_quality(self):
        self.assertEqual(score(self.case('numeric',{'answer':'18'}),503,{'message':'Unavailable'}),{'expected_status':False})

    def test_code_is_parsed_without_execution(self):
        case=self.case('code',{'function':'square'})
        result=score(case,200,{'response':'```python\ndef square(n):\n    raise RuntimeError("Never executed")\n```'})
        self.assertTrue(all(result.values()))
        self.assertFalse(score(case,200,{'response':'```python\ndef square(\n```'})['python_syntax'])

    def test_papers_require_known_title_not_just_nonempty_results(self):
        case=self.case('papers',{'title':'Attention Is All You Need'});case['payload']={'limit':5}
        body={'papers':[{'title':'Different paper','url':'https://arxiv.org/abs/1234'}]}
        self.assertTrue(score(case,200,body)['result_contract'])
        self.assertFalse(score(case,200,body)['known_title_at_k'])

    def test_stream_error_does_not_pass_on_http_200(self):
        response=Mock(status_code=200,headers={'content-type':'application/x-ndjson'})
        response.iter_lines.return_value=iter([b'{"type":"start","agent":"advocate"}',b'{"type":"error","message":"Failed"}'])
        response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        with patch('evaluation.run.requests.post',return_value=response):
            result=execute(self.case('numeric',{'answer':'18'}),1,'http://localhost',10)
        self.assertFalse(result['passed']);self.assertFalse(result['stream_completed'])
        self.assertEqual(result['http_status'],200)

    def test_schema_failure_and_expected_rejection(self):
        self.assertFalse(score(self.case('quiz'),200,{'quiz':{}})['pydantic_schema'])
        case=self.case('status');case['expected_status']=403
        self.assertTrue(all(score(case,403,{'message':'Blocked'}).values()))
        self.assertFalse(all(score(case,503,{'message':'Unavailable'}).values()))
