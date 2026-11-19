# Chat commands, Google ADK and prompt safety

The shared chat composer offers commands on both `/chatbot` and existing chat pages. Type `/` to browse, use arrow keys to select, Enter or Tab to insert, and Escape to dismiss. Commands accept text only; ordinary chat continues to support attachments. Results use the existing Markdown chat renderer and are saved with the conversation. Only the final battleground answer is saved; live role cards remain transient.

| Command | Workflow | Input |
| --- | --- | --- |
| `/agent-battleground` | LangGraph Advocate, Critic and Judge; streamed contributions | Question |
| `/summarize` | Google ADK summary editor using NVIDIA Nemotron | Source text |
| `/research` | LangGraph scholarly search and relevance selection; up to five linked papers | Question, at most 500 characters |
| `/quiz` | LangChain structured study service; three questions with answers | Topic or notes |
| `/flashcards` | LangChain structured study service; five question/answer cards | Topic or notes |

The browser sends a validated `command` separately from the plain `content`; Next.js forwards it as `command` alongside `prompt`. No slash prefix reaches the generation model. `/api/debate` forwards battleground to `/generate-debate`; the other commands use `/api/chat` and `/generate`. Python validates the same command identifiers for JSON and multipart requests. Unknown, empty, attached and misrouted commands are rejected. Non-battle commands use the current prompt as their source; they do not summarize the entire chat history. The composer allows 4,000 characters; direct Python commands allow 10,000 except research.

## Google ADK ownership

`services/adk_summary.py` implements a real ADK `LlmAgent`, `Runner` and `InMemorySessionService`. Each request gets a separate session, discarded after completion. The custom `BaseLlm` adapter forwards text messages to the existing NVIDIA transport; no Gemini account or Google API key is required. The adapter explicitly rejects tool calls and non-text content. ADK does not own persistent chat history. The direct endpoint is `POST /generate-summary` with `{"prompt":"source text"}`; its response includes `engine: "google-adk"`.

LangGraph continues to own research, tool agents and debate; CrewAI continues to own script writing. Google ADK 2.14.1 requires the compatible Starlette update pinned in `requirements.txt`. See the [official ADK model adapter contract](https://github.com/google/adk-python/blob/v2.14.1/src/google/adk/models/base_llm.py).

## Prompt screening

Before public AI routes run, `services/guardrails.py` classifies the prompt, current diagram code and supplied session history, or the Studio topic/Research query. It uses the configured NVIDIA Nemotron with deterministic sampling and strict JSON decision validation. The policy screens instruction overrides, hidden-prompt/credential extraction, data exfiltration and requests facilitating harmful actions, while permitting educational and defensive discussion.

- A blocked request returns HTTP 403 with a safe explanation.
- Provider errors, a 30-second deadline or malformed verdicts return HTTP 503. Generation does not proceed.
- Serialized screening input over 100,000 characters returns HTTP 413. Shorten the input or begin another conversation.
- Health checks and OCR-only extraction do not require model screening.
- Next.js preserves safe upstream messages/statuses. Chat and tool chat save both messages in one transaction after successful generation, so blocked requests create no partial exchange.

This is a model-based input filter, not a guarantee against prompt injection or harmful output. It adds a cloud-model call and latency. It does not inspect binary attachments, extracted attachment content, retrieved webpages/transcripts, generated output or tool results. Those remain untrusted inputs to the existing specialist prompts; comprehensive document/tool-result and output safety needs separate qualification. The guard does not provide API authentication or replace tool URL restrictions. No Llama model is activated.

## Conda execution and verification

Run from `microservice/`:

```bash
conda run -n sophianet-venv python -m pip install -r requirements.txt
./scripts/run.sh
./scripts/test.sh
conda run -n sophianet-venv python -m pip check
```

The scripts explicitly invoke Conda `sophianet-venv`, regardless of the shell's active Python. `NVIDIA_API_KEY` is required for both guard classification and generation.

Verification on 2026-11-19: 54 backend tests; real ADK runner tests use fake model responses and check concurrent isolation. Live NVIDIA calls succeeded for all four new commands and the three debate roles. A live secret-extraction prompt was blocked, while ordinary learning and defensive prompt-injection discussion were allowed. These examples are not a safety accuracy benchmark. Authenticated browser checks verified landing-page handoff, existing-chat commands, persistence/reload, five research links, unchanged stored history after a 403, and keyboard selection/filtering/Escape at desktop and mobile widths. TypeScript, command/error-forwarding checks, tool-state checks and targeted new-code lint passed. OAuth login itself and production load were not tested.
