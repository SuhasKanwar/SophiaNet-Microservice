"""Opt-in live checks. Run from microservice with Conda sophianet-venv; providers are called."""
import base64
import io
import json
import os
import time

import requests
from PIL import Image, ImageDraw, ImageFont

base = os.getenv('TEST_API_URL', 'http://127.0.0.1:8000')
checks = []


def check(path, payload=None):
    started = time.monotonic()
    response = requests.post(base + path, json=payload, timeout=240) if payload is not None else requests.get(base + path, timeout=10)
    assert response.status_code == 200, f'{path}: HTTP {response.status_code}'
    data = response.json()
    checks.append({'path': path, 'status': response.status_code, 'seconds': round(time.monotonic() - started, 2)})
    print(json.dumps(checks[-1]), flush=True)
    return data


if __name__ == '__main__':
    check('/health')
    check('/generate', {'prompt': 'Explain gravity in one sentence.'})
    answer = check('/generate-chat', {'prompt': 'What is the project codename in the attached note?', 'files': [{'filename': 'fixture.txt', 'content': 'The project codename is ORCHID-742.'}]})
    assert 'ORCHID-742' in answer['response']
    image = check('/generate-image', {'prompt': 'A watercolor sunflower in a blue vase'})
    assert image['image_url'].startswith('https://') and '.s3.' in image['image_url']
    stored = requests.get(image['image_url'], timeout=30)
    stored.raise_for_status()
    png = stored.content
    assert Image.open(io.BytesIO(png)).size == (512, 512)
    fixture = Image.new('RGB', (900, 160), 'white')
    ImageDraw.Draw(fixture).text((20, 30), 'SOPHIANET OCR TEST', fill='black', font=ImageFont.load_default(size=42))
    buffer = io.BytesIO(); fixture.save(buffer, format='PNG')
    ocr = check('/process-ocr', {'files': [{'filename': 'fixture.png', 'content': base64.b64encode(buffer.getvalue()).decode()}]})
    assert 'SOPHIANET' in ocr['response']
    video = check('/crawl-youtube', {'prompt': 'Summarize https://www.youtube.com/watch?v=jNQXAC9IVRw'})
    assert video['response'].strip()
    assert check('/generate-diagram', {'prompt': 'A flowchart from rain to river to ocean'})['response'].strip()
    assert len(check('/generate-quiz', {'topic': 'Basic arithmetic'})['quiz']['questions']) == 3
    print('Live API checks passed. Success checks response contracts, not factual quality.')
