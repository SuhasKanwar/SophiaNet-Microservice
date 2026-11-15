# Learning studio and system verification

The Learning Studio is available in the chatbot sidebar at `/chatbot/t/studio`.

- **Practice quiz:** enter a topic or paste study notes to generate three multiple-choice questions. Choose answers, check the score and explanations, or retry. Answers stay hidden until submission. Markdown downloads include the answer key.
- **Narration script:** enter a subject, audience and desired length. The existing CrewAI writer/editor workflow returns a script with scenes and spoken text.
- **Code script:** describe the program and language. Generated code is displayed and downloadable, never executed by the studio.

All three modes use authenticated `/api/studio`, with server-side validation, request cancellation forwarding and a three-minute upstream timeout. Script modes call `/generate-script`; quizzes call `/generate-quiz`. No database schema change or new package is required by these features. Studio results are page-local: download them before leaving the page. They are not saved as chat messages.

Quiz output is validated with Pydantic before display: exactly three questions, four distinct nonblank options, an answer index from zero to three and an explanation. If the model returns invalid JSON or quiz structure, one correction attempt is allowed. A second failure produces the existing safe upstream-error response. During live testing, a response included JSON-schema `$defs`; this failure motivated the bounded correction and its regression test. Schema validity does not establish factual correctness.

## Repeatable checks

Start Python from the microservice directory:

```bash
conda run --no-capture-output -n sophianet-venv uvicorn app:app --host 127.0.0.1 --port 8000
```

Start the web app from the web directory:

```bash
npm run dev -- --port 3001
```

Run offline backend tests from microservice:

```bash
conda run -n sophianet-venv python -m unittest discover -s tests -q
```

Run the opt-in live Python checks from microservice:

```bash
conda run --no-capture-output -n sophianet-venv python scripts/check_api.py
```

This calls real providers and checks health, routed chat, attachment retrieval, local image generation, OCR, YouTube processing, diagrams and quizzes. `TEST_API_URL` can override localhost:8000. Successful responses do not prove factual quality, especially with incomplete YouTube transcripts.

Run the opt-in authenticated checks from web:

```bash
node --env-file=.env scripts/check-system.mjs
```

This uses the configured database, NVIDIA credentials and session secret. It creates a uniquely named temporary user, signs a short-lived session using the existing application secret, exercises chat, debate, persisted history, Studio, diagrams and access controls, then removes only its fixture user and cascading conversations. It does not exercise Google OAuth. `TEST_BASE_URL` can override localhost:3001; use a local development instance with matching environment settings. A process killed before cleanup can leave its fixture account behind.

## Verification scope

34 backend tests pass. TypeScript and lint for the added Studio and live-check files pass. Live authenticated HTTP checks confirmed database writes and reloads, debate stream persistence, quiz/script/diagram generation, anonymous rejection and conversation ownership checks. Real browser checks confirmed quiz creation/scoring/retry/download, code-script creation, mobile width and debate completion with a real session and NVIDIA responses. Temporary browser/account fixtures were removed.

The full repository lint check fails in existing source and generated Prisma code. It is not a clean repository-wide lint result. No Google OAuth login, production build, load/soak test, learning-outcome evaluation or proof of model factual accuracy is claimed. The remote database had an intermittent connection failure on a later check; one successful run does not establish service availability. These current checks supersede earlier documentation saying database persistence had not been exercised.
