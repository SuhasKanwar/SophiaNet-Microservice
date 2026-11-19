"""Run a frozen dataset against real HTTP endpoints, persisting each attempt."""
import argparse
import concurrent.futures
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests
from PIL import Image

from config.models import NVIDIA
from evaluation.score import score

ROOT=Path(__file__).resolve().parent


def execute(case, repeat, base, timeout):
    started=time.perf_counter()
    record={'case_id':case['id'],'group':case['group'],'persona':case['persona'],'prompt_style':case['prompt_style'],
            'repeat':repeat,'endpoint':case['endpoint'],'scorer':case['scorer'],'expected_status':case['expected_status'],
            'started_at':datetime.now(timezone.utc).isoformat(),'events':[],'error_type':None,'cost_usd':None,'token_usage':None}
    try:
        with requests.post(base+case['endpoint'],json=case['payload'],timeout=(10,timeout),stream=True) as response:
            record['http_status']=response.status_code
            if 'application/x-ndjson' in response.headers.get('content-type',''):
                lines=[]
                for line in response.iter_lines(chunk_size=1):
                    if not line: continue
                    lines.append(line.decode('utf-8'))
                    if sum(map(len,lines))>2_000_000: raise ValueError('Response exceeds evaluation limit')
                    event=json.loads(line)
                    record['events'].append({'received_seconds':round(time.perf_counter()-started,4),**event})
                record['raw_response']='\n'.join(lines)+'\n'
                final=next((item for item in reversed(record['events']) if item.get('type')=='done'),None)
                record['body']={'response':final['text']} if final else {}
                record['stream_completed']=final is not None and not any(item.get('type')=='error' for item in record['events'])
            else:
                chunks=[]; size=0
                for chunk in response.iter_content(65536):
                    size+=len(chunk)
                    if size>2_000_000: raise ValueError('Response exceeds evaluation limit')
                    chunks.append(chunk)
                raw=b''.join(chunks).decode('utf-8',errors='replace')
                record['raw_response']=raw
                try: record['body']=json.loads(raw)
                except ValueError: record['body']={'unparsed_text':raw}
            record['checks']=score(case,response.status_code,record['body'])
            if 'stream_completed' in record:
                record['checks']['stream_completed']=record['stream_completed']
                record['checks']['panel_order']=[e['agent'] for e in record['events'] if e.get('type')=='contribution']==['advocate','critic','judge']
            if case['scorer']=='image' and response.status_code==200 and record['checks'].get('s3_url'):
                # Inspect generated images in memory; never save model-generated images locally.
                try:
                    stored=requests.get(record['body']['image_url'],timeout=30)
                    stored.raise_for_status()
                    image=Image.open(io.BytesIO(stored.content)); image.load()
                    record['checks']['stored_image_readable']=image.size==(512,512)
                except Exception as error:
                    record['checks']['stored_image_readable']=False
                    record['image_read_error']=type(error).__name__
    except Exception as error:
        record['error_type']=type(error).__name__
        record.setdefault('http_status',None)
        record.setdefault('checks',{})['transport_completed']=False
    record['elapsed_seconds']=round(time.perf_counter()-started,4)
    record['passed']=bool(record['checks']) and all(record['checks'].values())
    record['availability_failure']=record['http_status'] in (429,500,502,503,504) or record['error_type'] is not None
    return record


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',type=Path,default=ROOT/'datasets/system-v1.jsonl')
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    parser.add_argument('--repeats',type=int,default=2)
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--timeout',type=int,default=240)
    args=parser.parse_args()
    if args.repeats<1 or not 1<=args.workers<=4: parser.error('Positive repeats and 1–4 workers required')
    data=args.dataset.read_bytes(); cases=[json.loads(line) for line in data.decode().splitlines() if line.strip()]
    if len({case['id'] for case in cases})!=len(cases): raise ValueError('Duplicate case IDs')
    health=requests.get(args.base_url+'/health',timeout=10);health.raise_for_status()
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    directory=ROOT/'results'/run_id;directory.mkdir(parents=True,exist_ok=False)
    (directory/'dataset.jsonl').write_bytes(data)
    versions={}
    for name in ['google-adk','crewai','langgraph','langchain-openai','fastapi','pydantic','torch','matplotlib']:
        try: versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: versions[name]=None
    metadata={'run_id':run_id,'started_at':datetime.now(timezone.utc).isoformat(),'base_url':args.base_url,
              'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
              'dirty_before_run':bool(subprocess.check_output(['git','status','--porcelain'],text=True).strip()),
              'dataset_sha256':hashlib.sha256(data).hexdigest(),'cases':len(cases),'repeats':args.repeats,
              'workers':args.workers,'seed':20261120,'request_timeout_seconds':args.timeout,
              'python':sys.executable,'platform':platform.platform(),'cpu_count':os.cpu_count(),
              'model':NVIDIA['MODEL_NAME'],'model_settings':NVIDIA,'packages':versions,
              'architecture':'current implemented workflows; no unimplemented pattern comparison',
              'execution':'live HTTP, real configured model and tools; no provider mocks',
              'cost_note':'Provider token usage and billed rates are not exposed by these endpoints; cost is unknown. Local run, no AWS deployment cost measured.'}
    (directory/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    jobs=[(case,repeat) for repeat in range(1,args.repeats+1) for case in cases]
    random.Random(20261120).shuffle(jobs)
    started=time.perf_counter()
    with (directory/'attempts.jsonl').open('a') as output, concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(execute,case,repeat,args.base_url,args.timeout) for case,repeat in jobs]
        for index,future in enumerate(concurrent.futures.as_completed(futures),1):
            record=future.result()
            output.write(json.dumps(record,ensure_ascii=False)+'\n');output.flush()
            print(json.dumps({'done':index,'total':len(jobs),'case':record['case_id'],'repeat':record['repeat'],'status':record['http_status'],'pass':record['passed'],'seconds':record['elapsed_seconds']}),flush=True)
    metadata.update(finished_at=datetime.now(timezone.utc).isoformat(),wall_seconds=round(time.perf_counter()-started,3),completed_attempts=len(jobs))
    (directory/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(f'RESULTS={directory}',flush=True)


if __name__=='__main__': main()
