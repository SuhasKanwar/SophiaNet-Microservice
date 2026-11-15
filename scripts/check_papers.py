"""Opt-in live scholarly-source checks; no API key or LLM calls required."""
import os
import requests

base = os.getenv('TEST_API_URL', 'http://localhost:8000')

if __name__ == '__main__':
    for query in ('retrieval augmented generation', 'CRISPR gene editing'):
        response = requests.post(base + '/search-papers', json={'query': query, 'since': 2020, 'limit': 5}, timeout=40)
        assert response.status_code == 200, f'HTTP {response.status_code}'
        result = response.json()
        assert result['papers'], 'No live matches'
        assert all(paper['year'] >= 2020 for paper in result['papers'])
        assert len({paper['url'] for paper in result['papers']}) == len(result['papers'])
        assert all(paper['url'].startswith(('http://', 'https://')) for paper in result['papers'])
        print(query, ':', len(result['papers']), 'papers; sources:', result['sources_searched'], '; warnings:', result['warnings'], flush=True)
    invalid = requests.post(base + '/search-papers', json={'query': ' ', 'limit': 50}, timeout=10)
    assert invalid.status_code == 422
    print('Live paper discovery and validation checks passed; relevance and factual quality are not benchmarked.')
