# Reproducible current-system evaluation

The frozen suite contains 40 cases: eight questions from the **first eight GSM8K test rows**, plus 32 synthetic fixtures covering current SophiaNet workflows. It is a small application evaluation, not a full GSM8K benchmark, an educational-outcome study or an evaluation of unimplemented architecture alternatives.

GSM8K source: [original repository](https://github.com/openai/grade-school-math), [dataset paper](https://arxiv.org/abs/2110.14168). Its MIT notice and selected originals are retained in `sources/`; `datasets/manifest.json` records the exact upstream revision, selection rule and SHA-256 digests. Synthetic fixtures are offered under [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/). Inputs and scoring rules were prepared before the live run. Do not rebuild the frozen dataset to replace an unfavorable result.

Run from `microservice/`, with the API already running via `./scripts/run.sh`:

```bash
conda run -n sophianet-venv python -m pip install -r evaluation/requirements.txt
conda run -n sophianet-venv python -m unittest discover -s tests -p test_evaluation.py -v
conda run --no-capture-output -n sophianet-venv python -m evaluation.run --repeats 2 --workers 2
conda run -n sophianet-venv python -m evaluation.report evaluation/results/<run-id>
```

The live runner invokes real NVIDIA and tool endpoints, including image/S3 and public scholarly/video services. It never executes generated code, saves generated images locally, mocks providers or automatically retries failed attempts. Two repeats produce 80 attempts. Seeded random ordering and two workers are recorded; first-use downloads/warm-up and provider variability affect timings.

Every attempted case is flushed to append-only JSONL with raw responses, checks, status, elapsed time and public stream events. Each result directory includes the exact dataset snapshot, environment/configuration metadata, CSV, summary JSON, Markdown report, measured latency boxplot and acceptance heat map. Observed debate role intervals are plotted when available and explicitly identified as proxies rather than callback spans.

Checks differ by workflow: numeric exact-match, source fact coverage, schema validity, AST syntax/function presence, diagram declaration/labels, known-title retrieval, clean-input OCR, video topic coverage, S3 readback or expected rejection. The aggregate is an **acceptance-check rate**, not general accuracy. No independent hallucination, pedagogy or image-quality score is implied. Details and denominators appear in each report.

Dollar cost/token usage remain unknown because the application drops aggregate model usage and account rates are not supplied. Do not fill missing costs with zeros. No AWS deployment, framework migration, architecture comparison or human/LLM-judge study is performed by this harness. Authenticated browser verification is stored separately in the web repository.

## Recorded results

See [current-system results](results/comparison/README.md) for the completed traffic protocols, stored raw observations and plots. These runs are not the proposed architecture-comparison study.

The original scoring missed the valid Tuesday/Tuesdays variant. `scoring_errata.json` records the correction; run `python -m evaluation.rescore <result-directory>` inside Conda before regenerating a report to produce a separate corrected view without replacing raw outputs. For a paced run use `--repeats 1 --workers 1 --interval 6`. To regenerate the protocol comparison use `python -m evaluation.compare <first-result-directory> <paced-result-directory>`.
