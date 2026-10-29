# Models and AI infrastructure

[Documentation index](README.md) · [Architecture](system_architecture.md) · [Research](research/README.md)

Configuration is grounded in [models.py](../microservice/config/models.py), [prompts.py](../microservice/config/prompts.py) and the corresponding model/service implementations at microservice commit `eb4caa3`.

## Model inventory

| Component | Exact configured model | Provider/execution | Role and selection |
| --- | --- | --- | --- |
| Text generation | `nvidia/nemotron-3.5-lightning-30b-a3b` | NVIDIA hosted API | Active default for research chat, Mermaid and transcript summaries; overridable through `NVIDIA_MODEL` |
| Request classification | Same NVIDIA model | NVIDIA hosted API | Active text/image classifier, with separate JSON-output settings |
| Primary image generation | `black-forest-labs/FLUX.1-dev` | Hugging Face InferenceClient, provider `fal-ai` | Active primary image path; returned label `flux` |
| Fallback image generation | `stability.sd3-5-large-v1:0` | AWS `bedrock-runtime`, `us-west-2` | Active fallback image path; returned label `stable_diffusion` |
| Text embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Local Hugging Face/Sentence Transformers, CPU | Active when attachments require vector retrieval; anonymous public-model download |
| Image captioning | `Salesforce/blip-image-captioning-base` | Local Transformers/PyTorch | Active image-attachment caption path; loaded lazily |
| Image-text diagnostic | `openai/clip-vit-base-patch32` | Local Transformers/PyTorch | Active image-generation scoring path; not a retrieval index or OpenAI API request |
| OCR | Installed Tesseract engine | Local system executable via `pytesseract` | Active OCR utility; no exact engine/language-data version pinned by the repository |
| Legacy chat | `llama-3.3-70b-versatile` | Retained Groq/Llama code | Inactive; no running route imports `models/llama.py` |
| Legacy classifier settings | `meta-llama/llama-4-scout-17b-16e-instruct` | Retained `LLAMA_ROUTER_MODEL` configuration | Inactive; preserved for reference |

The collection combines language generation, semantic text embeddings, image synthesis, image captioning, image-text similarity and OCR. These are distinct models with distinct inputs. The project does not train or fine-tune them, and it does not implement a common multimodal foundation model.

Research papers are foundations rather than exact reports for every deployed model version. In particular, the Nemotron 3 Nano paper is not a report for the configured 3.5 Lightning endpoint; the original latent-diffusion paper is not a full specification of FLUX.1 or Stable Diffusion 3.5. See the [literature review](literature_review.md) for the distinction.

## NVIDIA cloud inference

[models/nvidia.py](../microservice/models/nvidia.py) creates a `ChatOpenAI` client with NVIDIA credentials and NVIDIA's base URL. The client library's name does not make NVIDIA requests OpenAI-hosted. All active language requests go to `https://integrate.api.nvidia.com/v1` through Chat Completions, with `use_responses_api=False` and thinking disabled through `chat_template_kwargs`.

| Setting | Default |
| --- | --- |
| Credential | `NVIDIA_API_KEY` |
| Model override | `NVIDIA_MODEL` |
| Temperature / top-p | `0.6` / `0.95` |
| Output token limit | `4096` |
| Client timeout | `90` seconds |
| Client retries | `2` |
| Router override | Temperature `0`, output limit `256`, JSON object response |
| Graph recursion limit | `16` |

The classifier response is validated against `classification: text | image` and optional `image_description`, rejecting unexpected fields. JSON mode helps constrain syntax; it does not prove the classification is correct. Classification is a separate call outside the research graph.

The earlier implementation session observed HTTP 410 for `nvidia/nemotron-3-nano-30b-a3b` and selected the currently configured Lightning model after a live check. This is a historical receipt, not a permanent guarantee of provider availability.

## Agent and prompt responsibilities

[AssistantService](../microservice/services/assistant.py) constructs three compiled graphs from one [graph builder](../microservice/agents/graph.py):

| Agent | System instructions | Available tools |
| --- | --- | --- |
| `research` | Educational answers in Markdown, source use, uncertainty and treating retrieved content as untrusted | Wikipedia, arXiv, DuckDuckGo, website retrieval, YouTube transcripts |
| `diagram` | Return only complete Mermaid code without fences | None |
| `youtube` | Structure the supplied transcript into summary, concepts, lecture notes and review questions; acknowledge missing content | None |

The research graph binds tools to the NVIDIA client. Model-emitted tool calls route to `ToolNode`; their results return to the model. Tool errors are supplied as error messages so the agent can try a different source or explain the unavailable evidence. The recursion limit bounds graph transitions. There is no background multi-agent team, learned supervisor, persistent checkpointer or autonomous long-running job scheduler.

System prompts guide output; they are not factuality validators, security isolation or a proof that citations are correct. The video and diagram agents share the provider but use their own instructions. The image model prompt constants are retained, but the current image-generation implementations send sanitized user prompt text rather than a chat sequence containing those `SystemMessage` objects.

## Research tools

| Tool | Implementation | Boundaries |
| --- | --- | --- |
| Wikipedia | LangChain `WikipediaQueryRun`, HTTPS API and SophiaNet user agent | Defaults: top 3 results, 1,000 content characters |
| arXiv | `ArxivQueryRun` and `ArxivAPIWrapper` | Defaults: top 3 results, 1,000 content characters; summaries are not automatic full-paper verification |
| DuckDuckGo | `DuckDuckGoSearchResults` and search API wrapper | Default 3 results; availability and source quality vary |
| `scrape_website` | Requests plus BeautifulSoup | Public HTTP(S), DNS/redirect validation, 15-second request timeout, 1 MB download limit, 12,000 output characters |
| `youtube_transcript` | `youtube-transcript-api` | English preference; 60,000-character tool output cap with a truncation marker |

Website retrieval removes script, style, navigation and footer elements. It does not execute a browser, bypass authentication or guarantee access to JavaScript-rendered content. DNS validation has a documented rebinding limitation. The YouTube endpoint retrieves and summarizes a transcript directly, without the research agent's tool-output truncation stage.

## Document retrieval pipeline

The text assistant creates a new `RAGService` only when the current request includes files. It extracts documents, splits them using `RecursiveCharacterTextSplitter`, embeds them with MiniLM and creates a FAISS index. The current defaults are 1,000-character chunks, 150-character overlap and a retrieval count of four. Retrieved passages include source filenames.

The embedding model is cached; the FAISS store is request-local in the active text path. Public embeddings explicitly use `token=False` and `device=cpu`, avoiding implicit Hugging Face authentication and requiring no compatible CUDA GPU. This prevents the earlier configured-token and local-GPU issues in this particular path. It does not change Flux's credential requirements.

| Attachment | Current extraction |
| --- | --- |
| PDF | `pypdf` text extraction per page; no scanned-PDF OCR fallback |
| TXT / MD | UTF-8 decoding with invalid bytes ignored |
| PNG / JPG / JPEG | BLIP caption converted to a text document |

A failed or empty extraction can be skipped by file helpers. There is no durable document ingestion queue, document catalog, reranker, hybrid lexical retrieval, citation-to-page mapping or cross-turn index reuse. The image providers also inherit `RAGService` and invoke retrieval, but discard the retrieved context and history before generating; attachment-conditioned image synthesis is therefore not implemented.

## Image captioning and processing

[ImageCaptioningService](../microservice/services/image_captioning.py) opens images as RGB and applies this sequence before BLIP:

1. Gaussian blur, radius 1.
2. Contrast enhancement by 1.2, brightness by 1.1 and sharpness by 1.3.
3. Edge detection through Pillow `FIND_EDGES`, blended into the image with weight 0.2.
4. Grayscale conversion, contrast enhancement by 1.5, then conversion back to three-channel RGB.
5. BLIP generation with `max_new_tokens=50`.

Despite method names and comments, these operations are not learned object detection, semantic segmentation or adaptive thresholding. No ablation establishes that they improve caption quality. They can remove color information or alter detail. The separate OCR path sends images directly to Tesseract and does not reuse this BLIP preprocessing pipeline.

## Image generation and storage

[Image dispatch](../microservice/services/images.py) constructs providers lazily, tries Flux first and uses Stable Diffusion on failure. The models sanitize role prefixes, Markdown fences and repeated whitespace. The `MAX_TOKENS` values of 100 for Flux and 77 for Stable Diffusion currently cap **characters**, because `_trim_prompt` uses Python string length rather than tokenization.

Flux retries a failed generation once with safer prompt wording. Stable Diffusion performs its safer-wording retry for a detected prompt-filter failure. A failed primary provider, including initialization failure, then allows the dispatcher to try the fallback.

Generated images are encoded as PNG and passed to [S3Syncer](../microservice/utils/s3_syncer.py). The configured bucket is `sophianet`, with prefix `generated-images/`. The helper uses UUID object names for prefix-style keys and defaults to a `public-read` ACL. Real operation depends on bucket ownership/ACL/public-access settings and credentials. There is no signed-URL access layer, retention policy or user-specific object ownership record in this implementation.

CLIP loads when the image-provider modules are imported. It evaluates `logits_per_image / 100` and clamps the result to `[0,1]`. This is an implementation-specific diagnostic, not a calibrated probability or a direct normalized cosine similarity. The configured 512 embedding dimension is not used to build an image-search index.

## Infrastructure layers

| Layer | Main technologies | Responsibility |
| --- | --- | --- |
| Browser | React 19, Next.js pages, Tailwind, Mermaid, Web Speech APIs | Interaction and presentation |
| Web server | Next.js 15.5.2, NextAuth 4, Zod | Sessions, ownership checks, validation and provider forwarding |
| Persistence | PostgreSQL, Prisma 6 | Users, conversations and chat records |
| Python API | FastAPI 0.136.1, Pydantic 2.13.3, Uvicorn | Shared input validation, endpoint composition and error responses |
| AI orchestration | LangChain 1.2.15, LangGraph 1.1.9 | Model calls, tool schemas and graph execution |
| Local ML | Sentence Transformers 5.4.1, Transformers 5.6.2, PyTorch 2.11.0, FAISS CPU | Embeddings, captioning and image diagnostics |
| Cloud inference | NVIDIA, Hugging Face/fal-ai, AWS Bedrock | Language and image generation |
| Object storage | AWS S3 and boto3 | Generated image objects |
| Packaging | Conda environment, Python requirements, npm lockfile, Dockerfiles, Compose | Local dependencies and deployment descriptions |

Blocking model, retrieval and OCR calls are dispatched through Starlette's worker-thread interface from asynchronous endpoints. This keeps those calls off the event loop; it does not provide a durable queue, global spending cap, autoscaling or unlimited concurrency. Local models and indexes consume process memory, and each worker process maintains its own caches.
