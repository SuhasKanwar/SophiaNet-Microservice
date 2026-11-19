"""Deterministic, task-specific checks; no LLM judge or generated-code execution."""
import ast
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from services.study import FlashcardDeck, Quiz


def normalize(text):
    return ' '.join(re.findall(r'\w+', str(text).casefold()))


def contains(text, phrase):
    return f' {normalize(phrase)} ' in f' {normalize(text)} '


def score(case, status, body):
    checks = {'expected_status':status == case['expected_status']}
    kind, ref = case['scorer'], case['reference']
    if kind == 'status':
        checks['response_contract'] = isinstance(body,dict) and (bool(body.get('response')) if status==200 else isinstance(body.get('message'),str))
        return checks
    if status != 200:
        return checks
    if not isinstance(body,dict):
        return {**checks, 'json_object':False}
    text = body.get('response','')
    if kind == 'numeric':
        values = re.findall(r'FINAL_ANSWER[\s:*=_`]*\$?(-?[\d,]+(?:\.\d+)?)',str(text),re.I)
        try: checks['numeric_exact_match'] = bool(values) and Decimal(values[-1].replace(',','')) == Decimal(ref['answer'].replace(',',''))
        except InvalidOperation: checks['numeric_exact_match'] = False
    elif kind == 'facts':
        for index, aliases in enumerate(ref['facts']):
            checks[f'reference_fact_{index+1}'] = any(contains(text,item) for item in aliases)
    elif kind in ('quiz','flashcards'):
        try:
            (Quiz if kind=='quiz' else FlashcardDeck).model_validate(body['quiz' if kind=='quiz' else 'deck'])
            checks['pydantic_schema'] = True
        except (ValueError,KeyError,TypeError): checks['pydantic_schema'] = False
    elif kind == 'code':
        blocks=re.findall(r'```(?:python|py)\s*\n([\s\S]*?)```',str(text),re.I)
        candidate=blocks[0] if blocks else str(text)
        try:
            tree=ast.parse(candidate)
            checks['python_syntax'] = True
            checks['named_function'] = any(isinstance(node,ast.FunctionDef) and node.name==ref['function'] for node in ast.walk(tree))
        except SyntaxError: checks['python_syntax'] = False; checks['named_function'] = False
    elif kind == 'diagram':
        checks['diagram_declaration'] = bool(re.search(r'\b(flowchart|graph|sequenceDiagram)\b',str(text)))
        checks['required_labels'] = all(contains(text,label) for label in ref['labels'])
    elif kind == 'papers':
        papers=body.get('papers',[])
        checks['result_contract'] = isinstance(papers,list) and 0<len(papers)<=case['payload']['limit'] and all(isinstance(p,dict) and p.get('title') and urlsplit(p.get('url','')).scheme in ('http','https') for p in papers)
        checks['known_title_at_k'] = isinstance(papers,list) and any(normalize(p.get('title',''))==normalize(ref['title']) for p in papers if isinstance(p,dict))
    elif kind == 'ocr': checks['reference_text'] = contains(text,ref['text'])
    elif kind == 'image':
        url=body.get('image_url','')
        checks['s3_url'] = isinstance(url,str) and urlsplit(url).scheme=='https' and '.s3.' in (urlsplit(url).hostname or '')
    else: raise ValueError(f'Unknown scorer {kind}')
    return checks
