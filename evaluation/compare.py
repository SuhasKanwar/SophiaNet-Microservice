"""Compare completed traffic protocols without pooling them into an accuracy score."""
import argparse
import json
import statistics
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def compare(directories):
    output=Path(__file__).parent/'results/comparison';output.mkdir(exist_ok=True)
    runs=[]
    for directory in directories:
        metadata=json.loads((directory/'metadata.json').read_text())
        summary=json.loads((directory/'summary.json').read_text())
        filename='rescored_attempts.jsonl' if (directory/'rescored_attempts.jsonl').exists() else 'attempts.jsonl'
        records=[json.loads(line) for line in (directory/filename).read_text().splitlines()]
        if len(records)!=metadata['completed_attempts']: raise ValueError('Incomplete result set')
        runs.append(dict(directory=directory,metadata=metadata,summary=summary,records=records))
    if len({r['metadata']['dataset_sha256'] for r in runs})!=1: raise ValueError('Different datasets cannot be compared here')
    labels=[f"{r['metadata']['workers']} worker(s), {r['metadata'].get('minimum_start_interval_seconds',0)}s interval" for r in runs]
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    axes[0].boxplot([[row['elapsed_seconds'] for row in r['records']] for r in runs],tick_labels=labels,showmeans=True)
    axes[0].set(title='All attempts, including failures',ylabel='Client latency (seconds)')
    usable=[(label,[row['elapsed_seconds'] for row in r['records'] if row['passed']]) for label,r in zip(labels,runs)]
    usable=[(label,values) for label,values in usable if values]
    if usable: axes[1].boxplot([values for _,values in usable],tick_labels=[label for label,_ in usable],showmeans=True)
    axes[1].set(title='Attempts passing their task checks',ylabel='Client latency (seconds)')
    for ax in axes: ax.tick_params(axis='x',rotation=15)
    fig.suptitle('Different traffic protocols and time windows; descriptive, not causal')
    fig.tight_layout();fig.savefig(output/'protocol_latency_boxplots.png',dpi=160);plt.close(fig)
    table=['| Protocol | Attempts | Passed task checks | HTTP 5xx/transport failures | Wall seconds |','| --- | ---: | ---: | ---: | ---: |']
    for label,run in zip(labels,runs):
        summary=run['summary'];table.append(f"| {label} | {summary['attempts']} | {summary['passed']} | {summary['availability_failures']} | {summary['wall_seconds']} |")
    comparisons=[dict(run_id=r['metadata']['run_id'],workers=r['metadata']['workers'],minimum_start_interval_seconds=r['metadata'].get('minimum_start_interval_seconds',0),attempts=r['summary']['attempts'],passed=r['summary']['passed'],availability_failures=r['summary']['availability_failures'],wall_seconds=r['summary']['wall_seconds'],cost_usd=None) for r in runs]
    (output/'comparison.json').write_text(json.dumps(comparisons,indent=2)+'\n')
    links='\n'.join(f"- [{r['metadata']['run_id']} — full report](../{r['metadata']['run_id']}/REPORT.md)" for r in runs)
    body=f'''# Current-system evaluation results

The frozen dataset contains 40 cases: eight GSM8K test questions and 32 synthetic workflow fixtures. The two protocols below executed {sum(run['summary']['attempts'] for run in runs)} real API attempts in total, with original raw results retained. Results use transparent scoring v1.1 errata for the valid Tuesday/Tuesdays reference variant; original scores and inputs remain available. These are task-specific acceptance checks, not a general accuracy or learning-outcome score.

'''+ '\n'.join(table)+'''

The initial protocol has two repeats per case and two workers. Rate-limit failures are part of its result. The paced protocol runs every case once, with one worker and a minimum six-second start interval. It is a separately labeled run, not replacement retries. Counts must not be pooled into a single accuracy claim. Different time windows, stochastic generation, warm-up and overlapping static browser probes prevent a causal architecture/performance claim.

![Measured traffic-protocol latency](protocol_latency_boxplots.png)

'''+links+'''

Each run stores input snapshots, raw outputs and public debate contributions, status/check results, CSV, JSON, metadata, latency boxplots and heat maps. Cost/token usage are unknown because the endpoints do not expose aggregate billing usage; no zero-cost values or invented cost plots are supplied. The backend/scorer suite passes 62 tests; this test count is separate from live attempts.

## Findings and interpretation

- The initial API server log recorded 29 input-guard `RateLimitError` warnings, consistent with 29 HTTP 503 safety-screening failures. Do not interpret unavailable answers as independently measured factual errors. The guard correctly fails closed.
- Generated-image attempts fail with HTTP 502. The API server log identifies AWS `InvalidAccessKeyId`; image delivery remains blocked until valid S3 access is configured. No generated image was saved locally by the evaluator.
- Public math examples expose wrong numeric answers in some generations. Compare the original reference, final marker and public panel contributions in raw records; an HTTP 200 response or a multi-agent debate does not establish correctness.
- The very short video summary does not include the expected zoo topic. This is a strict topic-coverage failure, not proof that the entire summary is false; this fixture is too small to qualify lecture-summary quality.
- One benign synthetic document request was blocked during the initial protocol. This is a false-blocking example under the suite's stated policy, separate from rate limiting.
- Diagram parser results are supplemental to declaration/label checks. Quiz/flashcard checks establish schema validity, and code checks establish syntax/function presence without execution. Neither proves semantic correctness.
- Browser receipts in the web repository cover a real saved ADK summary, keyboard selection, rejection paths, reload, mobile fit and six tool routes. Duplicate main landmarks were observed. OAuth login, full accessibility and every tool interaction were not qualified.

## Scope and next work

This evaluates the currently implemented system on a small, nonrandom case selection with uncontrolled model training exposure. It does not evaluate a completed CrewAI/ADK-only migration, distributed Blackboard, MCP/A2A, the proposed balanced 240-run architecture study, AWS deployment or educational outcomes. Add independent reference/human review and usage instrumentation before making broader correctness/cost claims. Fix quota handling, S3 credentials and false-blocking cases separately, then record a new versioned run rather than overwriting these observations.
'''
    (output/'README.md').write_text(body)
    print(json.dumps(comparisons))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directories',type=Path,nargs=2)
    compare(parser.parse_args().directories)
