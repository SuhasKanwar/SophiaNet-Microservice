"""Summarize saved attempts; plots contain measured observations only."""
import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


RUBRICS = {
 'math':'Exact numeric answer after the requested FINAL_ANSWER marker; not full GSM8K accuracy.',
 'retrieval':'Presence of two reference facts from synthetic attached notes; not hallucination precision.',
 'summary':'Coverage of three reference facts; unsupported additions are not independently scored.',
 'quiz':'Existing Pydantic quiz schema; pedagogical/factual quality not independently scored.',
 'flashcards':'Existing Pydantic deck schema; pedagogical/factual quality not independently scored.',
 'narration':'Reference name and quantity coverage; not narration quality.',
 'code':'Python AST syntax and named function presence; code never executed, behavior not proven.',
 'diagram':'Declaration/required labels; see supplementary Mermaid validation when available.',
 'papers':'HTTP/source contract and known exact title within requested top-k; not general relevance.',
 'ocr':'Normalized reference-text containment for clean synthetic inputs; not handwriting qualification.',
 'video':'Reference elephant/zoo topic coverage, not complete transcript-summary factuality.',
 'image':'S3 URL and readable in-memory 512x512 image; no visual/semantic quality score.',
 'safety':'Expected allow/block status and response shape on these fixtures; not a safety benchmark.',
 'validation':'Expected rejection status and safe response shape.'}


def percentile(values, fraction):
    values=sorted(values)
    position=(len(values)-1)*fraction
    low=math.floor(position);high=math.ceil(position)
    return values[low]+(values[high]-values[low])*(position-low)


def generate(directory):
    metadata=json.loads((directory/'metadata.json').read_text())
    result_file=directory/('rescored_attempts.jsonl' if (directory/'rescored_attempts.jsonl').exists() else 'attempts.jsonl')
    records=[json.loads(line) for line in result_file.read_text().splitlines()]
    groups=defaultdict(list)
    for record in records: groups[record['group']].append(record)
    summary={'attempts':len(records),'cases':len({r['case_id'] for r in records}),'passed':sum(r['passed'] for r in records),
             'availability_failures':sum(r['availability_failure'] for r in records),
             'http_status_counts':dict(Counter(str(r['http_status']) for r in records)),
             'wall_seconds':metadata.get('wall_seconds'),'cost_usd':None,'token_usage':None,'groups':{}}
    for group,items in sorted(groups.items()):
        durations=[r['elapsed_seconds'] for r in items]
        checks=defaultdict(lambda:dict(evaluated=0,passed=0))
        for record in items:
            for name,value in record['checks'].items():
                checks[name]['evaluated']+=1;checks[name]['passed']+=bool(value)
        summary['groups'][group]={'attempts':len(items),'passed':sum(r['passed'] for r in items),
                                 'availability_failures':sum(r['availability_failure'] for r in items),
                                 'p50_seconds':round(statistics.median(durations),3),'p95_seconds':round(percentile(durations,.95),3),
                                 'checks':dict(checks),'rubric':RUBRICS[group]}
    with (directory/'attempts.csv').open('w',newline='') as file:
        names=['case_id','group','persona','prompt_style','repeat','endpoint','expected_status','http_status','passed','availability_failure','elapsed_seconds','error_type','cost_usd','token_usage']
        writer=csv.DictWriter(file,fieldnames=names,extrasaction='ignore');writer.writeheader();writer.writerows(records)
    labels=sorted(groups)
    fig,ax=plt.subplots(figsize=(13,6))
    ax.boxplot([[r['elapsed_seconds'] for r in groups[group]] for group in labels],tick_labels=labels,showmeans=True)
    ax.set(ylabel='Observed client wall time (seconds)',title='Current-system latency by workflow — all attempts, including failures')
    ax.tick_params(axis='x',rotation=45);fig.tight_layout();fig.savefig(directory/'latency_boxplot.png',dpi=160);plt.close(fig)
    ids=sorted({r['case_id'] for r in records}); repeats=sorted({r['repeat'] for r in records})
    matrix=np.full((len(ids),len(repeats)),np.nan)
    for record in records: matrix[ids.index(record['case_id']),repeats.index(record['repeat'])]=float(record['passed'])
    fig,ax=plt.subplots(figsize=(7,13));plot=ax.imshow(matrix,aspect='auto',vmin=0,vmax=1,cmap='RdYlGn')
    ax.set_yticks(range(len(ids)),ids);ax.set_xticks(range(len(repeats)),[f'Repeat {r}' for r in repeats]);ax.set_title('Task acceptance checks: 0 fail, 1 pass\nHeterogeneous checks; not a common quality score')
    fig.colorbar(plot,ax=ax);fig.tight_layout();fig.savefig(directory/'case_results_heatmap.png',dpi=150);plt.close(fig)
    stage_rows=[]
    for record in records:
        starts={};durations={}
        for event in record['events']:
            if event.get('type')=='start': starts[event['agent']]=event['received_seconds']
            if event.get('type')=='contribution' and event['agent'] in starts: durations[event['agent']]=event['received_seconds']-starts[event['agent']]
        if durations: stage_rows.append((f"{record['case_id']} r{record['repeat']}",durations))
    if stage_rows:
        names=['advocate','critic','judge'];data=[[row.get(name,np.nan) for name in names] for _,row in stage_rows]
        fig,ax=plt.subplots(figsize=(8,4));plot=ax.imshow(data,aspect='auto',cmap='YlOrRd')
        ax.set_xticks(range(3),names);ax.set_yticks(range(len(stage_rows)),[name for name,_ in stage_rows]);ax.set_title('Debate stages: observed event intervals\nProxy timings, not instrumented agent spans')
        for y,row in enumerate(data):
            for x,value in enumerate(row):
                if not math.isnan(value): ax.text(x,y,f'{value:.2f}s',ha='center',va='center')
        fig.colorbar(plot,ax=ax,label='seconds');fig.tight_layout();fig.savefig(directory/'debate_stage_heatmap.png',dpi=160);plt.close(fig)
        summary['debate_observed_stage_seconds']=[{'attempt':name,**durations} for name,durations in stage_rows]
    (directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    rows=['| Workflow | Attempts | Passed checks | Availability failures | p50 s | p95 s |','| --- | ---: | ---: | ---: | ---: | ---: |']
    for group,item in summary['groups'].items(): rows.append(f"| {group} | {item['attempts']} | {item['passed']} | {item['availability_failures']} | {item['p50_seconds']} | {item['p95_seconds']} |")
    failures=['| Case / repeat | HTTP | Failed checks |','| --- | ---: | --- |']
    for record in records:
        if not record['passed']: failures.append(f"| {record['case_id']} / {record['repeat']} | {record['http_status']} | {', '.join(name for name,value in record['checks'].items() if not value)} |")
    scoring_note='Scoring v1.1 applies the documented Tuesday/Tuesdays reference-alias correction; original attempts/checks are unchanged. See [scoring errata](scoring_errata.json) and [rescored observations](rescored_attempts.jsonl).' if result_file.name.startswith('rescored') else 'Original frozen scoring; no post-run corrections applied.'
    text=f'''# SophiaNet current-system evaluation — {metadata['run_id']}

## Protocol and provenance

Live HTTP evaluation of {summary['cases']} cases with {metadata['repeats']} repeats: **{len(records)} attempts**. Concurrency: {metadata['workers']}; minimum start interval: {metadata.get('minimum_start_interval_seconds',0)} seconds; seeded execution order: {metadata['seed']}. Total wall time: {metadata.get('wall_seconds')} seconds. Environment/model/settings are recorded in [metadata.json](metadata.json); exact input payloads are in [dataset.jsonl](dataset.jsonl). Public cases are the first eight test rows of GSM8K; 32 synthetic cases extend application coverage. See [dataset provenance](../../datasets/manifest.json) and the [GSM8K MIT notice](../../sources/gsm8k-LICENSE.txt).

This evaluates current implemented workflows. It does not compare unimplemented Blackboard/P2P or sequential/parallel/hierarchical variants, certify AWS deployment, or reproduce a full public benchmark. Persona tags and varied prompts are heterogeneous coverage, not a balanced causal persona experiment.

## Results

{scoring_note}

**{summary['passed']}/{len(records)} attempts passed all case-specific acceptance checks.** This aggregate mixes schema, fact-coverage, exact-answer and expected-rejection checks; it is NOT a system accuracy score. **{summary['availability_failures']} attempts had transport/upstream availability failures.** Expected 400/403 rejections can pass. HTTP 200 streaming errors fail. Provider failures are retained, not silently rerun or removed.

'''+ '\n'.join(rows)+'''

Latency includes guard, model/tool calls, queueing and transport. Percentiles are descriptive for this small suite and concurrency, not production SLOs. All-attempt boxplots include failures, which may return faster or slower than successful generations.

![Latency boxplots](latency_boxplot.png)

![Case acceptance heatmap](case_results_heatmap.png)

## What each check measures

'''+ '\n'.join(f'- **{name}:** {rubric}' for name,rubric in RUBRICS.items())+'''

Per-check numerators/denominators are in [summary.json](summary.json). Checks evaluated only after HTTP 200 are conditional and exclude unavailable outputs; their evaluated count must always accompany any reported rate. Refer to all-attempt counts for availability-adjusted success.

## Failures

'''+ '\n'.join(failures)+'''

Full raw public responses, all streamed contributions, observed event times, statuses and failed checks are retained in [attempts.jsonl](attempts.jsonl); [attempts.csv](attempts.csv) supports analysis. No authentication headers or environment secrets are recorded. Generated model images are inspected in memory and remain on S3; plots here are evaluation charts, not saved model images.

## Cost, agent timing and limits

Billed cost and token usage are **unknown**, not zero: current endpoints omit aggregate usage across guard/router/agent/tool calls and no account billing rates are supplied. No cost boxplot is fabricated. Actual end-to-end runtimes are recorded; an honest dollar estimate requires those missing usage/rate inputs. Local compute and external NVIDIA inference were used; no AWS deployment was evaluated.

Debate role intervals, when available, are derived from public start/contribution arrival times and include scheduling/buffering effects. They are proxies, not callback-instrumented per-agent spans. ADK/CrewAI per-agent internal timings are not exposed and are not invented. The accompanying browser verification is separate from this direct API suite. Human educational review, citation support grading, full image semantics, generated-code execution, load testing and a calibrated LLM judge were not performed.
'''
    if stage_rows: text+='\n![Observed debate stage times](debate_stage_heatmap.png)\n'
    if (directory/'mermaid_validation.json').exists():
        extra=json.loads((directory/'mermaid_validation.json').read_text())
        text+=f"\n## Supplementary Mermaid parser validation\n\n{sum(item['valid'] for item in extra)}/{len(extra)} generated diagrams parsed with the installed frontend Mermaid library. See [parser receipts](mermaid_validation.json). Parsing does not establish factual or visual quality.\n"
    (directory/'REPORT.md').write_text(text)
    print(json.dumps({key:summary[key] for key in ('attempts','cases','passed','availability_failures','wall_seconds')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path)
    generate(parser.parse_args().directory)
