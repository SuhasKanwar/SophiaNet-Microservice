# Project objectives

[Documentation index](README.md) · [Features](features.md) · [Literature review](literature_review.md)

## Purpose

SophiaNet — “Network of Wisdom” — aims to reduce the friction between finding educational material and turning it into a useful explanation. Learning resources arrive as notes, text documents, images, websites and recorded lectures. The project provides a common conversation interface and dedicated utilities for these inputs, with model and tool selection behind a Python API.

The immediate objective is a practical educational and research assistant: ask a question, attach relevant material when available, retrieve supporting information when needed, and receive an explanation or visual artifact. The implementation combines existing models and libraries; it does not train a new foundation model or claim a new retrieval or agent algorithm.

## Problem addressed

A learner may need separate applications to read a document, extract text from a photograph, summarize a lecture, search for related papers, sketch a process diagram and generate an illustration. Those tools often lose conversation context between steps. SophiaNet puts these operations within one web workspace and stores the resulting conversation history.

The common interface does not mean every input shares one semantic representation. Documents use text embeddings, images become BLIP captions in the text retrieval path, and CLIP is used only for image-generation diagnostics. This is a coordinated collection of workflows rather than a fully unified multimodal index.

## Intended users

| User | Typical need | Relevant workflow |
| --- | --- | --- |
| Student | Understand a topic or a passage from supplied notes | Chat with attachments and follow-up questions |
| Independent learner | Turn a lecture transcript into an outline and review questions | YouTube transcript summary |
| Teacher or content author | Draft a process diagram or an illustration | Mermaid generation and image generation |
| Researcher | Locate introductory information and paper summaries | Research agent with arXiv, Wikipedia and web tools |
| Developer or evaluator | Inspect orchestration, latency and failure behavior | Python API, test suite and diagnostic metrics |

These are intended use cases, not evidence of usability, accessibility or learning gains from a user study.

## Concrete engineering objectives

### 1. Provide one usable workspace

Use Google sign-in, user-owned conversations and saved messages to keep interactions organized. Render Markdown, code blocks, generated images and Mermaid diagrams in the browser. Support speech input and output where browser APIs are available.

### 2. Ground answers in supplied or retrieved material

Extract text from supported uploads, split it into overlapping chunks, retrieve a small set of relevant passages, and give them to the language model. Expose research tools so the agent can obtain external information instead of relying only on pretrained knowledge. Ask the model to cite sources and acknowledge unavailable evidence.

The current system has no citation validator, entailment checker or formal grounding score. Prompt instructions express the objective; they do not enforce factual correctness.

### 3. Separate orchestration from provider code

Keep API parsing and routing separate from the language client, agent graph, retrieval service and image providers. Use NVIDIA-hosted Nemotron for all active language tasks. Preserve Llama source and configuration for reference without selecting it in a running path.

### 4. Support both explanations and visual outputs

Classify general requests as text or image, run a research agent for text, and use Flux with a Stable Diffusion fallback for image requests. Provide a specialist Mermaid prompt for structured diagram code. Caption image attachments for text-based discussion and provide a separate OCR utility for extracting visible text.

### 5. Make operational limits visible

Bound file sizes, supported types, history length, graph steps and website downloads. Keep per-request retrieval indexes separate. Return safe Python error messages when a provider fails. Expose process liveness separately from provider readiness, and document what has and has not been tested.

## Representative user journeys

### Ask about a document

1. Sign in and start a conversation.
2. Attach PDF, TXT, MD, PNG, JPG or JPEG files and ask a question.
3. The web server checks the conversation owner and forwards history and files to the Python service.
4. For a text request, the service builds a request-local FAISS index, retrieves up to four chunks and includes their source labels in the agent input.
5. The answer and model label are stored with the conversation; main chat also persists available performance metrics.

Only the files in the current request are indexed. Upload bytes and vector indexes are not persisted as a reusable document library. A later turn can use previous answer text as history but does not automatically retrieve from earlier attachments.

### Study a video

The YouTube tool creates a tool conversation, retrieves an available transcript and asks the video specialist for a structured summary. Its system prompt also requests important concepts and possible review questions. The underlying service uses transcripts, not video frame analysis, audio transcription or timestamp-grounded visual understanding.

### Create a diagram

Describe a diagram in the dedicated page. The browser sends the description and current Mermaid code to `/generate-diagram`; Nemotron returns code and the browser renders it with pan and zoom. A follow-up can refine that code. The dedicated page keeps its current diagram in component state; it does not use the standard chat persistence path.

### Generate an illustration

Ask for an image in general chat. The NVIDIA classifier selects the image path, the image provider generates a PNG, and S3 stores it. The browser displays the returned URL. Failures can trigger prompt retry and then provider fallback; a generated image is not proof of educational or scientific correctness.

## Contribution and differentiation

The defensible contribution at this stage is **system integration**: an educational interface combining document context, a real tool-execution loop, transcript analysis, OCR, diagrams, multiple image providers and conversation persistence. Request-local retrieval, explicit specialist prompts and separation of API/provider concerns are engineering choices that can be inspected in code.

No comparative experiment currently establishes that this combination is unique, more accurate, faster, cheaper or more effective for learning than existing assistants or the systems described in the research collection. The [literature review](literature_review.md) explains relationships to prior methods and identifies the measurements needed to support stronger claims.

## Success criteria and next evidence

| Objective | Current observable behavior | Evidence still needed |
| --- | --- | --- |
| Useful explanations | Text and retrieval paths exist | Expert-rated correctness, completeness and supported claims |
| Better study workflow | Multiple utilities share the application | Task completion time and usability study against a baseline |
| Reliable research tools | Tool results return through LangGraph | Source quality, citation accuracy, tool-selection success and failure rates |
| Safe multi-user use | Web ownership checks and isolated text indexes | End-to-end access-control, egress and resource-abuse testing |
| Useful visual artifacts | Diagram/image providers are connected | Mermaid parse rate, human image relevance ratings and image-provider proof |
| Educational benefit | Prompts target explanations and review questions | Controlled pre/post assessment, delayed retention and subgroup analysis |

Persistent knowledge libraries, OCR-to-summary orchestration, learner adaptation, slide/document export, text-to-video generation and a working image-filter utility remain possible extensions. They are outside the implemented scope documented here.
