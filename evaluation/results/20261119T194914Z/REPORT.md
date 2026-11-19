# SophiaNet current-system evaluation — 20261119T194914Z

## Protocol and provenance

Live HTTP evaluation of 40 cases with 1 repeats: **40 attempts**. Concurrency: 1; minimum start interval: 6.0 seconds; seeded execution order: 20261120. Total wall time: 356.406 seconds. Environment/model/settings are recorded in [metadata.json](metadata.json); exact input payloads are in [dataset.jsonl](dataset.jsonl). Public cases are the first eight test rows of GSM8K; 32 synthetic cases extend application coverage. See [dataset provenance](../../datasets/manifest.json) and the [GSM8K MIT notice](../../sources/gsm8k-LICENSE.txt).

This evaluates current implemented workflows. It does not compare unimplemented Blackboard/P2P or sequential/parallel/hierarchical variants, certify AWS deployment, or reproduce a full public benchmark. Persona tags and varied prompts are heterogeneous coverage, not a balanced causal persona experiment.

## Results

Scoring v1.1 applies the documented Tuesday/Tuesdays reference-alias correction; original attempts/checks are unchanged. See [scoring errata](scoring_errata.json) and [rescored observations](rescored_attempts.jsonl).

**36/40 attempts passed all case-specific acceptance checks.** This aggregate mixes schema, fact-coverage, exact-answer and expected-rejection checks; it is NOT a system accuracy score. **2 attempts had HTTP 429/5xx or transport failures (an operational bucket, not a diagnosis of every cause).** Expected 400/403 rejections can pass. HTTP 200 streaming errors fail. Provider failures are retained, not silently rerun or removed.

| Workflow | Attempts | Passed checks | HTTP 5xx/transport failures | p50 s | p95 s |
| --- | ---: | ---: | ---: | ---: | ---: |
| code | 1 | 1 | 0 | 3.674 | 3.674 |
| diagram | 3 | 3 | 0 | 0.86 | 0.902 |
| flashcards | 3 | 3 | 0 | 2.525 | 6.043 |
| image | 1 | 0 | 1 | 25.972 | 25.972 |
| math | 8 | 7 | 0 | 3.2 | 10.415 |
| narration | 1 | 1 | 0 | 7.167 | 7.167 |
| ocr | 2 | 2 | 0 | 0.193 | 0.236 |
| papers | 3 | 2 | 1 | 12.736 | 23.898 |
| quiz | 3 | 3 | 0 | 3.931 | 53.258 |
| retrieval | 4 | 4 | 0 | 1.315 | 1.415 |
| safety | 3 | 3 | 0 | 0.782 | 5.211 |
| summary | 4 | 4 | 0 | 1.651 | 2.049 |
| validation | 3 | 3 | 0 | 0.428 | 0.433 |
| video | 1 | 0 | 0 | 15.022 | 15.022 |

Latency includes guard, model/tool calls, queueing and transport. Percentiles are descriptive for this small suite and concurrency, not production SLOs. All-attempt boxplots include failures, which may return faster or slower than successful generations.

![Latency boxplots](latency_boxplot.png)

![Case acceptance heatmap](case_results_heatmap.png)

## What each check measures

- **math:** Exact numeric answer after the requested FINAL_ANSWER marker; not full GSM8K accuracy.
- **retrieval:** Presence of two reference facts from synthetic attached notes; not hallucination precision.
- **summary:** Coverage of three reference facts; unsupported additions are not independently scored.
- **quiz:** Existing Pydantic quiz schema; pedagogical/factual quality not independently scored.
- **flashcards:** Existing Pydantic deck schema; pedagogical/factual quality not independently scored.
- **narration:** Reference name and quantity coverage; not narration quality.
- **code:** Python AST syntax and named function presence; code never executed, behavior not proven.
- **diagram:** Declaration/required labels; see supplementary Mermaid validation when available.
- **papers:** HTTP/source contract and known exact title within requested top-k; not general relevance.
- **ocr:** Normalized reference-text containment for clean synthetic inputs; not handwriting qualification.
- **video:** Reference elephant/zoo topic coverage, not complete transcript-summary factuality.
- **image:** S3 URL and readable in-memory 512x512 image; no visual/semantic quality score.
- **safety:** Expected allow/block status and response shape on these fixtures; not a safety benchmark.
- **validation:** Expected rejection status and safe response shape.

Per-check numerators/denominators are in [summary.json](summary.json). Checks evaluated only after HTTP 200 are conditional and exclude unavailable outputs; their evaluated count must always accompany any reported rate. Refer to all-attempt counts for availability-adjusted success.

## Failures

| Case / repeat | HTTP | Failed checks |
| --- | ---: | --- |
| 33-video / 1 | 200 | reference_fact_2 |
| 08-math / 1 | 200 | numeric_exact_match |
| 28-papers / 1 | 502 | expected_status |
| 34-image / 1 | 502 | expected_status |

Full raw public responses, all streamed contributions, observed event times, statuses and failed checks are retained in [attempts.jsonl](attempts.jsonl); [attempts.csv](attempts.csv) supports analysis. No authentication headers or environment secrets are recorded. Generated model images are inspected in memory and remain on S3; plots here are evaluation charts, not saved model images.

## Cost, agent timing and limits

Billed cost and token usage are **unknown**, not zero: current endpoints omit aggregate usage across guard/router/agent/tool calls and no account billing rates are supplied. No cost boxplot is fabricated. Actual end-to-end runtimes are recorded; an honest dollar estimate requires those missing usage/rate inputs. Local compute and external NVIDIA inference were used; no AWS deployment was evaluated.

Debate role intervals, when available, are derived from public start/contribution arrival times and include scheduling/buffering effects. They are proxies, not callback-instrumented per-agent spans. ADK/CrewAI per-agent internal timings are not exposed and are not invented. The accompanying browser verification is separate from this direct API suite. Human educational review, citation support grading, full image semantics, generated-code execution, load testing and a calibrated LLM judge were not performed.

![Observed debate stage times](debate_stage_heatmap.png)

## Supplementary Mermaid parser validation

3/3 generated diagrams parsed with the installed frontend Mermaid library. See [parser receipts](mermaid_validation.json). Parsing does not establish factual or visual quality.
