# Agent battleground and script generation

The research assistant already includes LangChain tools for Wikipedia, arXiv, web search, website retrieval and YouTube transcripts. Two new tools check bounded arithmetic and search Crossref for publication titles and DOI links. Crossref metadata is not full-text evidence; network failures are returned through the existing tool error path.

## Debate

In an existing chat, type `/` and select `/agent-battleground`, then enter a question. Enter or Tab selects the command; Escape dismisses the picker. The command applies to that message only; ordinary messages use standard chat. The former header toggle has been removed. Text requests go through authenticated `/api/debate`, which checks conversation ownership and loads the last 20 text messages from the database. Attachments remain available in standard chat only.

Python `/generate-debate` runs a bounded LangGraph: Advocate → Critic → Judge. The first two roles can use the shared research tools; the Judge synthesizes their public contributions. All three use the configured NVIDIA model with different role prompts. They are not independent model families or private reasoning traces. The graph has a five-minute deadline and bounded inner tool loops.

The NDJSON stream emits `start`, `contribution`, and `done` events; failures emit `error`. Contributions stream when each role completes, rather than token by token. The web server relays progress, then atomically saves the user message and final answer and emits `saved`. An interrupted panel is not saved as a complete answer. Intermediate contributions appear in collapsible cards during the current page session but are not persisted or replayed after reload. Switching chats cancels the browser request. Provider work already in progress can take time to terminate.

This adds review opportunities, not proven accuracy gains. Shared models can repeat the same mistakes. No learning-outcome or answer-quality benchmark has been run. Extra model/tool calls increase latency and provider usage.

## Scripts

`POST /generate-script` accepts `{"prompt":"Explain the water cycle in 30 seconds","kind":"narration"}`. `kind` supports `narration` and `code`; narration is the default. Prompts must be nonblank and no longer than 10,000 characters. The endpoint returns the standard `response`, model and latency fields plus `engine: crewai`.

CrewAI owns a sequential writer/editor pair. A custom BaseLLM reuses the existing LangChain NVIDIA transport, with delegation, memory and caching disabled. These agents do not execute generated code or access the filesystem. CrewAI telemetry is disabled before import. Script generation is API-only; standard chat can also answer script-writing prompts, but does not automatically select CrewAI.

LangGraph remains the orchestration layer for research and debate. CrewAI is scoped to script writing. Google ADK was evaluated by dependency resolution but not added: its current dependency set replaces the pinned Starlette runtime and would duplicate session/orchestration ownership. Full CrewAI requires a larger dependency set than the existing graph; compatible Pydantic and related pins were updated and the environment passed `pip check`. All Python work used Conda `sophianet-venv`.

## Verification

- 31 backend tests pass, including graph order, safe stream errors, arithmetic rejection, script request validation and actual CrewAI execution with a fake model.
- Live NVIDIA: chat, routing, diagrams, all three debate roles, narration scripts and code scripts returned successful responses.
- Real OCR extracted a generated image fixture correctly. Local SD-Turbo image generation also passed after the CrewAI dependency update. The YouTube endpoint returned HTTP 200 with a transcript-quality notice; this does not establish summary quality.
- Live streamed debate events arrived at approximately 0.00s (start), 1.05s (Advocate), 2.17s (Critic), and 2.68s (Judge/final) for one arithmetic prompt. These timings are an example, not a latency benchmark.
- Crossref live lookup timed out after its 15-second request limit; successful live Crossref retrieval remains unverified.
- Browser checks with mocked authentication, upstream responses and persistence verified completed debate cards and final-answer rendering on desktop/mobile. The input overflow found on mobile was corrected.
- TypeScript and targeted endpoint lint pass. `pip check` passes.

Real Google OAuth, PostgreSQL persistence and disconnect behavior under production load have not been qualified. The Python API still has the existing unauthenticated boundary; the new web routes enforce session ownership. No Docker image was built and no changes were pushed.


## Slash command transport

The composer parses `/agent-battleground <question>` into `command: "agent-battleground"` and the plain question in `content`. Unknown commands, empty questions and attached files are rejected before sending, without clearing the composer. Only this command is offered. The web debate endpoint validates the command and forwards it separately as `command` alongside `prompt`; it never sends the slash prefix to the model. Python validates allowed command values for JSON and multipart requests, and rejects battleground commands sent to ordinary generation endpoints. Older direct debate requests without a command remain supported.

Command UI checks cover picker selection, Escape, malformed commands, mobile layout and all streamed role cards using mocked persistence/upstream. Forty backend tests cover structured-command validation and workflow behavior. TypeScript and targeted new-file lint pass. Intermediate debate cards remain page-local; only the final answer is persisted, as described above.
