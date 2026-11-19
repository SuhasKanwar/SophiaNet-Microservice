import unittest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app import app
from services.guardrails import guard_request
from services.papers import search_papers, crossref, arxiv, safe_url


def paper(title='A study',doi='10.1/test',year=2024,abstract=''):
    return dict(title=title,doi=doi,year=year,abstract=abstract,authors=['Author'],venue='Venue',url='https://doi.org/'+str(doi),pdf_url=None)


class PaperTests(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides[guard_request] = lambda: None
        self.addCleanup(app.dependency_overrides.pop, guard_request, None)
    def test_fusion_deduplicates_and_enriches(self):
        first=paper(); second={**paper(abstract='Evidence'),'pdf_url':'https://arxiv.org/pdf/1234'}
        with patch('services.papers.crossref',return_value=[first,first, paper('Other','10.1/other')]),patch('services.papers.arxiv',return_value=[second]):
            data=search_papers('topic')
        self.assertEqual(len(data['papers']),2)
        best=data['papers'][0]
        self.assertEqual(best['sources'],['Crossref','arXiv'])
        self.assertEqual(best['abstract'],'Evidence')
        self.assertTrue(best['pdf_url'])
        self.assertEqual(best['rank'],1)

    def test_partial_failure_and_year_filter(self):
        with patch('services.papers.crossref',return_value=[paper(year=2010),paper('New','10.1/new',2024)]),patch('services.papers.arxiv',side_effect=RuntimeError('secret')):
            data=search_papers('topic',2020,1)
        self.assertEqual(len(data['papers']),1)
        self.assertEqual(data['papers'][0]['title'],'New')
        self.assertEqual(data['sources_searched'],['Crossref'])
        self.assertNotIn('secret',str(data))
        self.assertTrue(data['warnings'])
        with patch('services.papers.crossref',side_effect=RuntimeError()),patch('services.papers.arxiv',side_effect=RuntimeError()):
            with self.assertRaises(RuntimeError):search_papers('topic')

    def test_crossref_normalization(self):
        response=Mock();response.json.return_value={'message':{'items':[{'type':'journal-article','title':['<i>Study</i>'],'DOI':'10.1234/ABC','published':{'date-parts':[[2024]]},'abstract':'&lt;p&gt;Evidence&lt;/p&gt;'}]}}
        response.json.return_value['message']['items'].append({'type':'book','title':['Book'],'DOI':'10.1/book'})
        with patch('services.papers.requests.get',return_value=response) as get:
            data=crossref('topic',2020)
        self.assertEqual(len(data),1)
        self.assertEqual(data[0]['title'],'Study'); self.assertEqual(data[0]['abstract'],'Evidence')
        self.assertEqual(data[0]['doi'],'10.1234/abc')
        self.assertIn('from-pub-date',get.call_args.kwargs['params']['filter'])

    def test_arxiv_normalization_and_url_safety(self):
        response=Mock();response.content=b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/1234.5678v1</id><title>A study</title><published>2024-01-01</published><summary>Evidence</summary><author><name>Author</name></author><link title="pdf" href="http://arxiv.org/pdf/1234.5678v1"/></entry></feed>'''
        with patch('services.papers.requests.get',return_value=response): data=arxiv('topic',None)
        self.assertEqual(data[0]['year'],2024);self.assertTrue(data[0]['pdf_url'].startswith('https://'))
        for url in ('javascript:alert(1)','file:///etc/passwd','https://user:pass@example.com'):
            self.assertIsNone(safe_url(url))

    def test_endpoint_validation_empty_and_failure(self):
        empty={'papers':[],'warnings':[],'sources_searched':['Crossref'],'query':'topic','ranking':'rank'}
        with patch('api.routes.papers.search_papers',return_value=empty),TestClient(app) as client:
            self.assertEqual(client.post('/search-papers',json={'query':'topic'}).json()['papers'],[])
            for payload in ({'query':' '},{'query':'a'},{'query':'x'*501},{'query':'topic','since':9999},{'query':'topic','limit':30}):
                self.assertEqual(client.post('/search-papers',json=payload).status_code,422)
        with patch('api.routes.papers.search_papers',side_effect=RuntimeError('secret')),TestClient(app) as client:
            result=client.post('/search-papers',json={'query':'topic'})
            self.assertEqual(result.status_code,502);self.assertNotIn('secret',result.text)
