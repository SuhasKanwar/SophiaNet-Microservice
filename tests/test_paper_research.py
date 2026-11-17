import json
import unittest
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage
from services.paper_research import PaperResearch


def candidate():
    return {'title':'Verified record','url':'https://doi.org/10.1/test','year':2024,'abstract':'Evidence','venue':'Journal','rank':1}


class PaperResearchTests(unittest.TestCase):
    def model(self, selections):
        model=Mock();model.bind.return_value=model
        model.invoke.side_effect=[AIMessage(content=json.dumps({'search_query':'solar energy','focus':'School energy'})),AIMessage(content=json.dumps({'selections':selections}))]
        return model

    def test_plan_retrieve_select_keeps_source_records(self):
        model=self.model([{'candidate_id':0,'relevance':'Matches school energy.'}])
        with patch('services.paper_research.search_papers',return_value={'papers':[candidate()],'warnings':[],'sources_searched':['Crossref']}) as search:
            data=PaperResearch(model).search('What powers a school?',2020,5)
        search.assert_called_once_with('solar energy',2020,20)
        self.assertEqual(data['papers'][0]['url'],candidate()['url'])
        self.assertEqual(data['query'],'What powers a school?')
        self.assertEqual(data['papers'][0]['relevance'],'Matches school energy.')

    def test_invalid_ids_and_duplicates_are_rejected(self):
        for selections in ([{'candidate_id':99,'relevance':'Fake'}],[{'candidate_id':0,'relevance':'a'},{'candidate_id':0,'relevance':'b'}]):
            with patch('services.paper_research.search_papers',return_value={'papers':[candidate()]}):
                model = self.model(selections)
                model.invoke.side_effect = [*model.invoke.side_effect, AIMessage(content=json.dumps({'selections': selections}))]
                with self.assertRaises(ValueError):PaperResearch(model).search('question')

    def test_no_candidates_skips_selection_call(self):
        model=self.model([])
        with patch('services.paper_research.search_papers',return_value={'papers':[],'warnings':[],'sources_searched':['arXiv']}):
            self.assertEqual(PaperResearch(model).search('question')['papers'],[])
        self.assertEqual(model.invoke.call_count,1)

    def test_extra_review_field_is_corrected_once(self):
        model=self.model([])
        model.invoke.side_effect=[
            AIMessage(content=json.dumps({'search_query':'solar','focus':'School energy'})),
            AIMessage(content=json.dumps({'selections':[], 'review':{'selections':[]}})),
            AIMessage(content=json.dumps({'selections':[{'candidate_id':0,'relevance':'Matches energy.'}]})),
        ]
        with patch('services.paper_research.search_papers',return_value={'papers':[candidate()],'warnings':[],'sources_searched':['Crossref']}):
            data=PaperResearch(model).search('School energy')
        self.assertEqual(data['papers'][0]['url'],candidate()['url'])
        self.assertEqual(model.invoke.call_count,3)

    def test_planner_invalid_json_is_corrected(self):
        model=self.model([])
        model.invoke.side_effect=[AIMessage(content='not json'),AIMessage(content=json.dumps({'search_query':'solar','focus':'School energy'}))]
        with patch('services.paper_research.search_papers',return_value={'papers':[],'warnings':[],'sources_searched':['Crossref']}):
            self.assertEqual(PaperResearch(model).search('School energy')['papers'],[])
        self.assertEqual(model.invoke.call_count,2)
