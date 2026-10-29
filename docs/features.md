# Features and implementation status

[Documentation index](README.md) · [Architecture](system_architecture.md)

“Implemented” describes a connected source path. Earlier integration checks are identified separately in [evaluation and limitations](evaluation_and_limitations.md).

## Feature matrix

| Feature | Current implementation | Status and practical limit |
| --- | --- | --- |
| Google sign-in | NextAuth Google provider, JWT sessions, Prisma user upsert | Implemented; requires OAuth configuration and database access |
| Conversation management | Create, list, rename and delete user-owned conversations | Implemented; deletion cascades to chats; archive field exists but no complete archive workflow is demonstrated |
| Text chat | NVIDIA Nemotron through the research graph | Implemented; provider credentials, quota and context limits apply |
| Automatic text/image routing | NVIDIA JSON classification validated by Pydantic | Implemented; routing considers the current prompt, not attached image pixels or full history |
| Conversation history | Browser supplies user/assistant messages per request | Implemented; no server-side LangGraph checkpointer |
| Document question answering | Extract, chunk, embed, FAISS top-four retrieval | Implemented for current-request attachments; no persistent document collection |
| Image attachments | Heuristic preprocessing and BLIP caption become text context | Partial multimodal support; the text model does not directly inspect uploaded pixels |
| Research agent | Wikipedia, arXiv, DuckDuckGo, website and YouTube tools | Implemented model/tool loop; no guarantee the model chooses the right tool or validates its result |
| Image generation | Flux primary, Stable Diffusion fallback, S3 upload | Implemented provider path; live generation/upload not qualified in the earlier session |
| OCR notes utility | Pillow opens images, Tesseract extracts text | Partial: returns extracted text, not the clean summary requested by the UI's default wording |
| YouTube summary | Available English transcript passed to specialist agent | Implemented; not audiovisual analysis or speech recognition |
| Mermaid diagrams | Specialist prompt returns diagram code; Mermaid renders SVG | Implemented; no backend syntax validator or automatic repair loop |
| Markdown and code rendering | MarkdownIt with raw HTML disabled, highlighted code component | Implemented UI behavior |
| Image preview/download | Modal display and download proxy | Implemented; download proxy lacks a URL allowlist and needs hardening |
| Speech input | Browser SpeechRecognition/WebKit API, English US | Implemented browser integration; support and recognition behavior vary by browser |
| Read aloud | Browser speechSynthesis after Markdown cleanup | Implemented browser integration; no dedicated speech model hosted by SophiaNet |
| Performance metrics | Latency, word count, lexical overlap, retrieval count, CLIP diagnostic | Implemented diagnostics; not a validated quality benchmark |
| Image filter | Page heading and tool variant only | Placeholder; `/image-filter` has no Python route |
| Text-to-video, slides and document export | Mentioned in product/landing aspirations | Proposed; no connected generation/export pipeline |
| Semantic image/video retrieval | CLIP configuration exists | Not implemented; CLIP currently scores generated images only |

## Python API

Routes live in [generation.py](../microservice/api/routes/generation.py), [tools.py](../microservice/api/routes/tools.py) and [health.py](../microservice/api/routes/health.py).

| Method | Path | Input | Successful response |
| --- | --- | --- | --- |
| GET | `/` | None | Welcome message and `status` |
| GET | `/health` | None | Process liveness and `status` |
| POST | `/generate` | Prompt, optional history/files | Text answer or image URL, model label, metrics; image path also returns classifier description |
| POST | `/generate-chat` | Prompt, optional history/files | `model: nvidia`, response text and metrics |
| POST | `/generate-image` | Prompt, optional history/files | `model: flux` or `stable_diffusion`, image URL and metrics |
| POST | `/process-ocr` | Files, optional prompt | Extracted text with `model: ocr`; prompt echoed |
| POST | `/crawl-youtube` | Prompt containing an HTTP(S) video URL, optional history | Transcript-based response with `model: nvidia` and metrics |
| POST | `/generate-diagram` | Prompt, optional current `code` and history | Mermaid code with `model: nvidia` and metrics |

The response uses `status`, `model`, `response`, `image_url` where relevant, and `performance_metrics`. Python input errors return HTTP 400 with a `message`; unexpected/provider failures return HTTP 502 with a generic message. `/health` does not check credentials, model availability, database access, Tesseract or image-provider readiness.

## Input rules

The shared [request parser](../microservice/api/requests.py) accepts JSON and multipart form data. Multipart uses `prompt`, JSON text in `session_history`, repeated `files` parts and optional `code`. JSON file objects use `filename` and base64 `content`; TXT/MD strings that are not valid base64 are treated as UTF-8 text.

| Constraint | Python service |
| --- | --- |
| File extensions | PDF, TXT, MD, PNG, JPG, JPEG |
| Number of files | At most 10 |
| File size | At most 10 MiB per file |
| History length | At most 200 messages |
| History roles | `user` and `assistant` |
| Prompt, code, per-message text | At most 100,000 characters each |
| Research graph | 16 graph steps, not 16 guaranteed tool executions |

The web chat schema has a separate 10,000-character content limit. The OCR utility internally recognizes more image extensions, but the shared API parser admits only the extensions above. A PDF sent to OCR is not automatically rasterized; PDF text extraction belongs to document retrieval.

Application limits do not replace gateway body-size, concurrency, authentication or provider-spend limits. Multipart files may be spooled by the framework before the application reads and checks them.

## Web API and persistence

| Web API | Responsibility |
| --- | --- |
| `/api/auth/[...nextauth]` | Google OAuth and session handling |
| `/api/conversation` | User-owned conversation listing, creation and deletion |
| `/api/rename-conversation` | Rename a conversation after checking ownership |
| `/api/chat` | Fetch/delete messages and forward chat generation after ownership validation |
| `/api/tool-conversation` | Create a typed tool conversation |
| `/api/tool-chat` | Dispatch notes, YouTube and diagram tool requests; image-filter mapping currently has no upstream implementation |
| `/api/download-image` | Fetch a supplied URL and return an attachment |

The main chat API stores `performanceMetrics` when returned. The current tool-chat API stores response text and model but does not persist returned performance metrics. Files are forwarded to the microservice, not stored as document records. Main chat saves the user message before provider generation; a failed provider request can therefore leave a user message without a bot reply.

The [dedicated diagram component](../web/src/components/tool/DiagramsTool.tsx) calls the Python service directly. Its current diagram/code remains in React component state. This path must be considered separately from the authenticated, persisted web API flow.

## Source navigation

- [Chat UI](../web/src/components/chat/ChatbotClient.tsx) and [message rendering](../web/src/components/chat/ChatMessages.tsx)
- [Notes utility](../web/src/components/tool/NotesTool.tsx), [YouTube utility](../web/src/components/tool/YoutubeVideoTool.tsx) and [diagram utility](../web/src/components/tool/DiagramsTool.tsx)
- [Speech recognition](../web/src/hooks/useSpeechRecognition.ts) and [speech synthesis](../web/src/hooks/useTextToSpeech.ts)
- [Database schema](../web/prisma/schema.prisma) and [web validation](../web/src/lib/schema.ts)
