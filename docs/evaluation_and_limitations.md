# Evaluation and limitations

[Documentation index](README.md) · [Literature review](literature_review.md) · [Operations](setup_and_operations.md)

SophiaNet currently has functional integration evidence and diagnostic metrics. It does not have a curated educational QA benchmark, controlled learning study, model comparison or calibrated end-to-end quality score. This distinction governs which claims the project can support.

## Evidence available before this documentation task

The preceding implementation session and [microservice README](../microservice/README.md) record the following results:

| Evidence | Earlier recorded result | Scope |
| --- | --- | --- |
| Python unittest suite | 22 tests passed | Compiled graph behavior, fake-provider API contracts, isolation, validation and fallback |
| Python compilation | Passed | Syntax/import compilation, not execution of all paths |
| Dependency consistency | `pip check` passed | Installed-package dependency compatibility |
| NVIDIA inference | Passed | A real hosted response |
| Text/image classifier | Passed | Simple example prompts classified through NVIDIA |
| LangGraph tool loop | Passed | Real NVIDIA tool-call, tool result and final response cycle |
| Main text endpoints | HTTP 200 | `/generate` and `/generate-chat` examples |
| Mermaid generation | HTTP 200 | Returned diagram code; no corpus-wide parse/syntax evaluation |
| YouTube summary | HTTP 200 | A real available transcript summarized |
| TXT attachment retrieval | HTTP 200 with expected codename and one retrieved chunk | One actual uploaded TXT example |
| Wikipedia, arXiv, search and website retrieval | Passed direct checks | Specific external requests, not long-term availability or source quality |
| HF credential metadata check | HTTP 401 | Earlier configured-token issue; credential values are not documented |

These are **earlier-session receipts**. The documentation task did not rerun the suite or live providers, and it did not verify current service health. Recorded successes do not establish production reliability, performance under load or general answer quality.

Live image generation/S3 upload, OCR execution, the full authenticated browser workflow, a web build/typecheck and Docker builds were not qualified in that earlier work. Image fallback and OCR endpoint wiring were checked using fakes.

## Documentation validation on 2026-10-30

All ten downloaded PDFs passed signature, readable-first-page and page-count checks, and their SHA-256 hashes and page counts matched the research catalogue. All 153 local Markdown link targets resolved. Nine Mermaid diagrams parsed and rendered to SVG using Mermaid 11.12.1 in local Chromium. These checks validate the documentation artifacts; application tests and provider calls were not rerun, and both application source repositories remained unchanged.

## What the current metrics measure

The [text metrics code](../microservice/services/assistant.py), [metric utilities](../microservice/utils/metrics.py) and image services expose diagnostics:

| Metric | Actual implementation | Interpretation limit |
| --- | --- | --- |
| `latency_ms` | Local elapsed time around the service's generation workflow | Text timing excludes the separate classifier call, web/database overhead and subsequent metric computation; not complete user-perceived latency |
| `response_length` | Whitespace-split word count | Length, not quality |
| `bleu_score` | Prompt treated as reference, generated response as hypothesis | Prompt-answer lexical overlap; not standard answer correctness evaluation |
| `rouge_l_score` | Prompt-response ROUGE-L | Overlap does not establish grounding or useful explanations |
| `retrieval_rouge_l` | Prompt-context ROUGE-L | Overlap with the question, not retrieval relevance against labeled relevant passages |
| `chunks_retrieved` | Number of passages returned | Retrieval count, not recall, precision or sufficient evidence |
| `clip_score` | CLIP image-text logit divided by 100, clamped to `[0,1]` | Uncalibrated diagnostic; not a probability, validated aesthetic score or direct cosine score |
| `image_size_bytes` | Encoded PNG byte length | Artifact size, not visual fidelity |
| `caption_bleu` | Optional prompt-caption overlap | Usually unavailable in the attachment path, which does not supply a reference caption |

A factually correct answer may have low overlap with its question. A copied or irrelevant answer may share many words with the prompt. Report these values as diagnostics with their computation, not as model accuracy, learning gain or a benchmark score. Image timing ends before CLIP metric computation, so that metric's overhead is also outside the recorded generation latency.

## Evaluation plan for stronger claims

This is proposed evaluation work, not a completed study.

| Question | Suggested experiment | Measures and controls |
| --- | --- | --- |
| Does retrieval improve answers? | Compare no retrieval, current retrieval and an improved retrieval baseline on the same labeled questions | Expert correctness, answer support, source attribution; fixed model/prompt and held-out questions |
| Are documents retrieved correctly? | Label relevant chunks for representative PDF/TXT/MD and caption-derived queries | Recall@k, precision@k, retrieval latency; include scanned PDFs and extraction failures |
| Does the agent use tools well? | Tasks requiring current facts, research lookup, unavailable sources and misleading results | Tool-selection success, grounded completion, source validity, number/cost of calls and failure recovery |
| Is routing reliable? | Labeled requests for images, image descriptions and ambiguous follow-ups | Text/image confusion matrix and downstream user impact |
| Are summaries faithful? | Human comparison of transcript summaries to the source transcript | Supported facts, omissions, invented claims and usefulness; include incomplete transcripts |
| Are diagrams usable? | A fixed set of diagram descriptions and refinements | Mermaid parse/render rate, constraint satisfaction and human readability |
| Do image heuristics help? | BLIP with original images versus each preprocessing stage and the full pipeline | Reference-caption measures and human semantic faithfulness; include color-sensitive examples |
| Does OCR work for the target material? | A versioned set of clean/noisy printed and handwritten note images | Character/word error rates with language and engine version recorded |
| Is the workflow educationally useful? | Consent-based study with a baseline workflow and a defined curriculum | Pre/post assessment, delayed retention, time-on-task and human review of explanations |
| Can the service handle demand? | Bounded concurrent requests with provider limits and failure injection | End-to-end p50/p95 latency, memory, throughput, cost, error rate and recovery |

Datasets, prompts, scoring rubrics, environment and provider/model version should be recorded together. Report sample sizes and uncertainty rather than transferring a research paper's benchmark results to this application.

## Current limitations and known gaps

### Grounding, knowledge and model behavior

The model can invent unsupported facts or citations despite prompt instructions. There is no automated citation validator, answer-to-evidence entailment check or verified bibliography builder in the runtime. Tool outputs and uploaded material are untrusted content, and prompt wording alone is not a complete prompt-injection defense.

Retrieval is a request-local text pipeline. Prior files are not automatically reindexed on later turns. Images are represented by BLIP captions rather than image embeddings. Extraction helpers can silently skip invalid or empty content. Scanned PDFs have no OCR fallback. The current chunking/retrieval settings have not been tuned against a labeled corpus, and there is no reranker or persistent document index.

The video workflow depends on available transcripts, prefers English variants and does not inspect video frames or transcribe audio. The dedicated endpoint does not implement a transcript chunk-and-merge summarization strategy, so sufficiently long transcripts can exceed provider context limits. Mermaid output is validated only by browser rendering, with no automated server repair.

### Images and digital processing

The preprocessing methods are blur, enhancement, edge blending and grayscale conversion. They do not implement object detection or segmentation despite method names/comments, and their claimed enhancement benefit has not been measured. Image providers compute inherited retrieval context but ignore it. Their `MAX_TOKENS` prompt caps currently count characters, which can discard substantial user intent.

CLIP scoring is uncalibrated and does not drive image retrieval or generation acceptance. Flux/Bedrock model access, S3 upload policy and local scoring dependencies still need live end-to-end qualification. The earlier HF-token error can affect provider readiness independently of NVIDIA text inference.

### Authentication, network access and privacy

[Next.js chat routes](../web/src/app/api/chat/route.ts) enforce session and conversation ownership, but the Python service has no authentication dependency. The direct browser diagram path and Next.js microservice rewrite do not inherit ownership checks. CORS accepts all origins with credentials enabled. A publicly reachable API can expose model usage and resource consumption without a gateway control.

The website tool validates public addresses and redirects but has a documented DNS-rebinding limit. Separately, [download-image](../web/src/app/api/download-image/route.ts) fetches an arbitrary supplied URL without authentication or a destination allowlist. From code inspection, this is a potential server-side request-forgery and resource-use risk if exposed to untrusted callers; it was not exploited or penetration-tested during documentation work.

Generated images default to public-read S3 ACLs. Image captioning logs generated captions, and error logs may contain provider details. No explicit data-retention, consent, deletion-of-S3-objects or private-document policy is implemented. Browser speech may involve browser/provider behavior beyond the application's own server, so it should not be described as guaranteed offline speech processing.

### Resource control and deployment

Worker-thread dispatch avoids blocking the async event loop but does not implement a durable queue, per-user quota, rate limit, cancellation budget or global concurrency control. A graph recursion cap does not bound the duration of every external request. Ten allowed 10 MiB uploads, large histories, local model caches and concurrent inference can still consume substantial resources.

Compose references published images rather than building the local source, has no database service or readiness checks and exposes the Python port. The Dockerfile lacks the OCR engine binary. Next.js deliberately ignores TypeScript and ESLint errors during builds. The current documentation therefore makes no reproducible-container or production-readiness claim.

### Incomplete product scope

The image-filter UI is a placeholder and its mapped upstream route does not exist. OCR returns extracted text rather than performing the summary promised by the default UI wording. Main chat persists metrics, while the tool-chat path does not. Dedicated diagrams are held in component state rather than persisted by that page's direct generation path. Text-to-video, slide/document export, learner adaptation, collaborative knowledge libraries and semantic image/video search remain proposed work.

## Defensible project claims

It is accurate to describe SophiaNet as a modular educational AI integration with NVIDIA language inference, LangGraph tool execution, request-local document retrieval, image providers, OCR, transcript summaries, Mermaid and conversation persistence. Earlier selected integration paths have successful receipts.

It is not yet supported to claim novel foundation models, superior factuality, guaranteed secure deployment, state-of-the-art OCR/image enhancement, measured learning gains or superiority to the ten reviewed research systems. The [literature review](literature_review.md) uses those papers to explain design choices and research gaps, not to substitute their results for project evaluation.
